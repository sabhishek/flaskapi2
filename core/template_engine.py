from jinja2 import Environment, FileSystemLoader, Template
import os
import yaml
from typing import Dict, Any
from flask import current_app
import logging

logger = logging.getLogger(__name__)

class TemplateEngine:
    """Template engine for generating Kubernetes manifests"""
    
    def __init__(self):
        self.templates_dir = current_app.config.get('TEMPLATES_DIR', 'templates')
        self.env = Environment(
            loader=FileSystemLoader(self.templates_dir),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Add custom filters
        self.env.filters['to_yaml'] = self._to_yaml_filter
    
    def _to_yaml_filter(self, value):
        """Custom Jinja2 filter to convert dict to YAML"""
        return yaml.dump(value, default_flow_style=False)
    
    def render_template(self, template_name: str, **kwargs) -> str:
        """Render template with given context"""
        try:
            template = self.env.get_template(template_name)
            return template.render(**kwargs)
        except Exception as e:
            logger.error(f"Failed to render template {template_name}: {e}")
            raise
    
    def render_from_string(self, template_string: str, **kwargs) -> str:
        """Render template from string"""
        try:
            template = Template(template_string)
            return template.render(**kwargs)
        except Exception as e:
            logger.error(f"Failed to render template from string: {e}")
            raise
    
    def get_template_list(self) -> list:
        """Get list of available templates"""
        try:
            templates = []
            for root, dirs, files in os.walk(self.templates_dir):
                for file in files:
                    if file.endswith(('.yaml', '.yml', '.j2')):
                        rel_path = os.path.relpath(os.path.join(root, file), self.templates_dir)
                        templates.append(rel_path)
            return templates
        except Exception as e:
            logger.error(f"Failed to get template list: {e}")
            return []