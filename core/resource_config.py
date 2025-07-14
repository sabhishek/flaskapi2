import yaml
import os
from typing import Dict, List, Optional
from dataclasses import dataclass
from flask import current_app

@dataclass
class WebhookConfig:
    enabled: bool = False
    url: str = ""
    mode: str = "single"  # single or staged
    timeout: int = 30
    retries: int = 3

@dataclass
class ResourceTypeConfig:
    name: str
    repo_url: str
    template_dir: str
    cluster_aware: bool = True
    async_processing: bool = True
    webhook: WebhookConfig = None
    flavors: List[str] = None

class ResourceConfigManager:
    """Manages dynamic resource type configuration"""
    
    def __init__(self):
        self.resource_types = {}
        self._load_default_config()
    
    def _load_default_config(self):
        """Load default resource type configurations"""
        default_configs = {
            'namespace': ResourceTypeConfig(
                name='namespace',
                repo_url='git@github.com:sabhishek/infra-templates.git',
                template_dir='namespaces/',
                cluster_aware=True,
                async_processing=True,
                webhook=WebhookConfig(
                    enabled=False,
                    url='https://webhook.example.com/namespace',
                    mode='single'
                ),
                flavors=['small', 'medium', 'large', 'custom']
            ),
            'vm': ResourceTypeConfig(
                name='vm',
                repo_url='https://github.com/org/vm-resources-gitops.git',
                template_dir='vms/',
                cluster_aware=False,
                async_processing=True,
                webhook=WebhookConfig(
                    enabled=True,
                    url='https://webhook.example.com/vm',
                    mode='single'
                ),
                flavors=['small', 'medium', 'large', 'custom']
            ),
            'osimage': ResourceTypeConfig(
                name='osimage',
                repo_url='https://github.com/org/os-image-builds-gitops.git',
                template_dir='osimage/',
                cluster_aware=False,
                async_processing=True,
                webhook=WebhookConfig(
                    enabled=True,
                    url='https://webhook.example.com/osimage',
                    mode='staged'
                ),
                flavors=['ubuntu-small', 'rhel-custom', 'custom']
            ),
            'misc': ResourceTypeConfig(
                name='misc',
                repo_url='https://github.com/org/misc-infra-gitops.git',
                template_dir='misc/',
                cluster_aware=True,
                async_processing=True,
                webhook=WebhookConfig(
                    enabled=True,
                    url='https://webhook.example.com/misc',
                    mode='single'
                ),
                flavors=['dns-record', 'certificate', 'secret', 'custom']
            )
        }
        
        self.resource_types.update(default_configs)
    
    def get_resource_config(self, resource_type: str) -> Optional[ResourceTypeConfig]:
        """Get configuration for a resource type"""
        return self.resource_types.get(resource_type)
    
    def list_resource_types(self) -> List[str]:
        """List all configured resource types"""
        return list(self.resource_types.keys())
    
    def add_resource_type(self, config: ResourceTypeConfig):
        """Add a new resource type configuration"""
        self.resource_types[config.name] = config
    
    def load_from_file(self, config_file: str):
        """Load resource configurations from YAML file"""
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config_data = yaml.safe_load(f)
                
            for name, data in config_data.get('resource_types', {}).items():
                webhook_data = data.get('webhook', {})
                webhook = WebhookConfig(**webhook_data) if webhook_data else None
                
                config = ResourceTypeConfig(
                    name=name,
                    repo_url=data['repo_url'],
                    template_dir=data['template_dir'],
                    cluster_aware=data.get('cluster_aware', True),
                    async_processing=data.get('async', True),
                    webhook=webhook,
                    flavors=data.get('flavors', ['custom'])
                )
                
                self.resource_types[name] = config