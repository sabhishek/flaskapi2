from jinja2 import Environment, Template
import yaml
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class TemplateEngine:
    """Template engine for generating infrastructure manifests"""
    
    def __init__(self):
        self.env = Environment(
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Add custom filters
        self.env.filters['to_yaml'] = self._to_yaml_filter
    
    def _to_yaml_filter(self, value):
        """Custom Jinja2 filter to convert dict to YAML"""
        return yaml.dump(value, default_flow_style=False)
    
    def render_template(self, template_content: str, **kwargs) -> str:
        """Render template with given context"""
        try:
            template = Template(template_content, environment=self.env)
            return template.render(**kwargs)
        except Exception as e:
            logger.error(f"Failed to render template: {e}")
            raise
    
    def render_manifest(self, template_content: str, name: str, tenant_id: str, 
                       cluster_id: str, spec: Dict, flavor: str = 'custom') -> str:
        """Render infrastructure manifest from template"""
        context = {
            'name': name,
            'tenant_id': tenant_id,
            'cluster_id': cluster_id,
            'flavor': flavor,
            'spec': spec,
            'labels': {
                'tenant.io/id': tenant_id,
                'managed-by': 'gitops-api',
                'flavor': flavor
            }
        }
        
        if cluster_id:
            context['labels']['cluster.io/id'] = cluster_id
        
        return self.render_template(template_content, **context)