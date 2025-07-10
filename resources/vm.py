from typing import Dict
from core.resource_manager import ResourceManager
from core.template_engine import TemplateEngine
import logging

logger = logging.getLogger(__name__)

class VMManager(ResourceManager):
    """Manager for Virtual Machine resources via Crossplane"""
    
    def __init__(self):
        super().__init__('vm')
        self.template_engine = TemplateEngine()
    
    def validate_spec(self, spec: Dict) -> bool:
        """Validate VM specification"""
        required_fields = ['name', 'instance_type', 'image']
        
        for field in required_fields:
            if field not in spec:
                logger.error(f"Missing required field: {field}")
                return False
        
        # Validate instance type
        valid_instance_types = ['t3.micro', 't3.small', 't3.medium', 't3.large', 
                               'm5.large', 'm5.xlarge', 'c5.large', 'c5.xlarge']
        
        if spec.get('instance_type') not in valid_instance_types:
            logger.error(f"Invalid instance type: {spec.get('instance_type')}")
            return False
        
        # Validate disk size
        disk_size = spec.get('disk_size', 20)
        if not isinstance(disk_size, int) or disk_size < 8 or disk_size > 1000:
            logger.error("Disk size must be between 8 and 1000 GB")
            return False
        
        return True
    
    def generate_manifest(self, name: str, spec: Dict, tenant_id: str) -> str:
        """Generate Crossplane VM manifest"""
        try:
            template_name = 'vm.yaml'
            
            context = {
                'name': spec.get('name', name),
                'tenant_id': tenant_id,
                'instance_type': spec.get('instance_type'),
                'image': spec.get('image'),
                'disk_size': spec.get('disk_size', 20),
                'key_name': spec.get('key_name', f"{tenant_id}-default"),
                'security_groups': spec.get('security_groups', []),
                'subnet_id': spec.get('subnet_id'),
                'tags': spec.get('tags', {}),
                'user_data': spec.get('user_data', '')
            }
            
            # Add tenant-specific tags
            context['tags'].update({
                'Tenant': tenant_id,
                'ManagedBy': 'gitops-api',
                'Environment': spec.get('environment', 'dev')
            })
            
            try:
                return self.template_engine.render_template(template_name, **context)
            except Exception:
                return self._generate_inline_manifest(context)
                
        except Exception as e:
            logger.error(f"Failed to generate VM manifest: {e}")
            raise
    
    def _generate_inline_manifest(self, context: Dict) -> str:
        """Generate manifest using inline template"""
        template_str = """apiVersion: ec2.aws.crossplane.io/v1alpha1
kind: Instance
metadata:
  name: {{ name }}
  namespace: {{ tenant_id }}
  labels:
    tenant.io/id: {{ tenant_id }}
    managed-by: gitops-api
spec:
  forProvider:
    instanceType: {{ instance_type }}
    imageId: {{ image }}
    keyName: {{ key_name }}
    {% if subnet_id %}
    subnetId: {{ subnet_id }}
    {% endif %}
    {% if security_groups %}
    securityGroupIds:
    {% for sg in security_groups %}
    - {{ sg }}
    {% endfor %}
    {% endif %}
    blockDeviceMappings:
    - deviceName: /dev/xvda
      ebs:
        volumeSize: {{ disk_size }}
        volumeType: gp3
        encrypted: true
        deleteOnTermination: true
    {% if user_data %}
    userData: |
{{ user_data | indent(6) }}
    {% endif %}
    tags:
{% for key, value in tags.items() %}
      {{ key }}: "{{ value }}"
{% endfor %}
  writeConnectionSecretsToNamespace: {{ tenant_id }}
"""
        return self.template_engine.render_from_string(template_str, **context)