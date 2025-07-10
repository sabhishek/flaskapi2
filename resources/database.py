from typing import Dict
from core.resource_manager import ResourceManager
from core.template_engine import TemplateEngine
import logging

logger = logging.getLogger(__name__)

class DatabaseManager(ResourceManager):
    """Manager for Database resources via Crossplane"""
    
    def __init__(self):
        super().__init__('database')
        self.template_engine = TemplateEngine()
    
    def validate_spec(self, spec: Dict) -> bool:
        """Validate database specification"""
        required_fields = ['name', 'engine', 'instance_class']
        
        for field in required_fields:
            if field not in spec:
                logger.error(f"Missing required field: {field}")
                return False
        
        # Validate engine
        valid_engines = ['mysql', 'postgres', 'mariadb', 'oracle-ee', 'sqlserver-se']
        if spec.get('engine') not in valid_engines:
            logger.error(f"Invalid database engine: {spec.get('engine')}")
            return False
        
        # Validate instance class
        valid_classes = ['db.t3.micro', 'db.t3.small', 'db.t3.medium', 'db.t3.large',
                        'db.m5.large', 'db.m5.xlarge', 'db.r5.large', 'db.r5.xlarge']
        if spec.get('instance_class') not in valid_classes:
            logger.error(f"Invalid instance class: {spec.get('instance_class')}")
            return False
        
        # Validate storage
        storage = spec.get('allocated_storage', 20)
        if not isinstance(storage, int) or storage < 20 or storage > 1000:
            logger.error("Allocated storage must be between 20 and 1000 GB")
            return False
        
        return True
    
    def generate_manifest(self, name: str, spec: Dict, tenant_id: str) -> str:
        """Generate Crossplane database manifest"""
        try:
            template_name = 'database.yaml'
            
            context = {
                'name': spec.get('name', name),
                'tenant_id': tenant_id,
                'engine': spec.get('engine'),
                'engine_version': spec.get('engine_version', ''),
                'instance_class': spec.get('instance_class'),
                'allocated_storage': spec.get('allocated_storage', 20),
                'storage_type': spec.get('storage_type', 'gp2'),
                'multi_az': spec.get('multi_az', False),
                'publicly_accessible': spec.get('publicly_accessible', False),
                'backup_retention_period': spec.get('backup_retention_period', 7),
                'backup_window': spec.get('backup_window', '03:00-04:00'),
                'maintenance_window': spec.get('maintenance_window', 'sun:04:00-sun:05:00'),
                'parameter_group': spec.get('parameter_group', ''),
                'security_groups': spec.get('security_groups', []),
                'subnet_group': spec.get('subnet_group', ''),
                'tags': spec.get('tags', {})
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
            logger.error(f"Failed to generate database manifest: {e}")
            raise
    
    def _generate_inline_manifest(self, context: Dict) -> str:
        """Generate manifest using inline template"""
        template_str = """apiVersion: rds.aws.crossplane.io/v1alpha1
kind: DBInstance
metadata:
  name: {{ name }}
  namespace: {{ tenant_id }}
  labels:
    tenant.io/id: {{ tenant_id }}
    managed-by: gitops-api
spec:
  forProvider:
    dbInstanceClass: {{ instance_class }}
    engine: {{ engine }}
    {% if engine_version %}
    engineVersion: {{ engine_version }}
    {% endif %}
    allocatedStorage: {{ allocated_storage }}
    storageType: {{ storage_type }}
    multiAZ: {{ multi_az | lower }}
    publiclyAccessible: {{ publicly_accessible | lower }}
    backupRetentionPeriod: {{ backup_retention_period }}
    preferredBackupWindow: {{ backup_window }}
    preferredMaintenanceWindow: {{ maintenance_window }}
    {% if parameter_group %}
    dbParameterGroupName: {{ parameter_group }}
    {% endif %}
    {% if security_groups %}
    vpcSecurityGroupIds:
    {% for sg in security_groups %}
    - {{ sg }}
    {% endfor %}
    {% endif %}
    {% if subnet_group %}
    dbSubnetGroupName: {{ subnet_group }}
    {% endif %}
    storageEncrypted: true
    deletionProtection: true
    tags:
{% for key, value in tags.items() %}
      {{ key }}: "{{ value }}"
{% endfor %}
  writeConnectionSecretsToNamespace: {{ tenant_id }}
  writeConnectionSecretToRef:
    name: {{ name }}-connection
    namespace: {{ tenant_id }}
"""
        return self.template_engine.render_from_string(template_str, **context)