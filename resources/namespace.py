from typing import Dict
from core.resource_manager import ResourceManager
from core.template_engine import TemplateEngine
import logging

logger = logging.getLogger(__name__)

class NamespaceManager(ResourceManager):
    """Manager for Kubernetes namespace resources"""
    
    def __init__(self):
        super().__init__('namespace')
        self.template_engine = TemplateEngine()
    
    def validate_spec(self, spec: Dict) -> bool:
        """Validate namespace specification"""
        required_fields = ['name']
        
        for field in required_fields:
            if field not in spec:
                logger.error(f"Missing required field: {field}")
                return False
        
        # Validate name format
        name = spec.get('name', '')
        if not name.replace('-', '').replace('_', '').isalnum():
            logger.error("Namespace name must be alphanumeric with hyphens/underscores")
            return False
        
        if len(name) > 63:
            logger.error("Namespace name must be 63 characters or less")
            return False
        
        return True
    
    def generate_manifest(self, name: str, spec: Dict, tenant_id: str) -> str:
        """Generate Kubernetes namespace manifest"""
        try:
            # Use template if available, otherwise generate directly
            template_name = 'namespace.yaml'
            
            context = {
                'name': spec.get('name', name),
                'tenant_id': tenant_id,
                'labels': spec.get('labels', {}),
                'annotations': spec.get('annotations', {}),
                'resource_quota': spec.get('resource_quota', {}),
                'network_policies': spec.get('network_policies', [])
            }
            
            # Add tenant-specific labels
            context['labels'].update({
                'tenant.io/id': tenant_id,
                'managed-by': 'gitops-api'
            })
            
            try:
                return self.template_engine.render_template(template_name, **context)
            except Exception:
                # Fallback to inline template if file doesn't exist
                return self._generate_inline_manifest(context)
                
        except Exception as e:
            logger.error(f"Failed to generate namespace manifest: {e}")
            raise
    
    def _generate_inline_manifest(self, context: Dict) -> str:
        """Generate manifest using inline template"""
        template_str = """apiVersion: v1
kind: Namespace
metadata:
  name: {{ name }}
  labels:
{% for key, value in labels.items() %}
    {{ key }}: "{{ value }}"
{% endfor %}
  annotations:
{% for key, value in annotations.items() %}
    {{ key }}: "{{ value }}"
{% endfor %}
---
{% if resource_quota %}
apiVersion: v1
kind: ResourceQuota
metadata:
  name: {{ name }}-quota
  namespace: {{ name }}
spec:
  hard:
{% for key, value in resource_quota.items() %}
    {{ key }}: "{{ value }}"
{% endfor %}
{% endif %}
"""
        return self.template_engine.render_from_string(template_str, **context)