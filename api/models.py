from flask_restx import fields
from flask_restx.namespace import Namespace

# API models for request/response serialization
def create_api_models(api):
    """Create API models for OpenAPI documentation"""
    
    # Base resource model
    resource_model = api.model('Resource', {
        'id': fields.String(required=True, description='Resource ID'),
        'name': fields.String(required=True, description='Resource name'),
        'resource_type': fields.String(required=True, description='Resource type'),
        'status': fields.String(required=True, description='Resource status'),
        'tenant_id': fields.String(required=True, description='Tenant ID'),
        'created_at': fields.DateTime(required=True, description='Creation timestamp'),
        'updated_at': fields.DateTime(required=True, description='Last update timestamp'),
        'spec': fields.Raw(description='Resource specification')
    })
    
    # Namespace specification
    namespace_spec = api.model('NamespaceSpec', {
        'name': fields.String(required=True, description='Namespace name'),
        'labels': fields.Raw(description='Namespace labels'),
        'annotations': fields.Raw(description='Namespace annotations'),
        'resource_quota': fields.Raw(description='Resource quota settings'),
        'network_policies': fields.List(fields.Raw, description='Network policies')
    })
    
    # VM specification
    vm_spec = api.model('VMSpec', {
        'name': fields.String(required=True, description='VM name'),
        'instance_type': fields.String(required=True, description='EC2 instance type'),
        'image': fields.String(required=True, description='AMI ID'),
        'disk_size': fields.Integer(description='Disk size in GB', default=20),
        'key_name': fields.String(description='SSH key pair name'),
        'security_groups': fields.List(fields.String, description='Security group IDs'),
        'subnet_id': fields.String(description='Subnet ID'),
        'tags': fields.Raw(description='Instance tags'),
        'user_data': fields.String(description='User data script')
    })
    
    # App specification
    app_spec = api.model('AppSpec', {
        'name': fields.String(required=True, description='Application name'),
        'image': fields.String(required=True, description='Container image'),
        'port': fields.Integer(required=True, description='Container port'),
        'replicas': fields.Integer(description='Number of replicas', default=1),
        'env_vars': fields.Raw(description='Environment variables'),
        'resources': fields.Raw(description='Resource requests and limits'),
        'labels': fields.Raw(description='Pod labels'),
        'annotations': fields.Raw(description='Pod annotations'),
        'service_type': fields.String(description='Service type', default='ClusterIP'),
        'ingress': fields.Raw(description='Ingress configuration'),
        'health_check': fields.Raw(description='Health check configuration')
    })
    
    # Database specification
    database_spec = api.model('DatabaseSpec', {
        'name': fields.String(required=True, description='Database name'),
        'engine': fields.String(required=True, description='Database engine'),
        'engine_version': fields.String(description='Engine version'),
        'instance_class': fields.String(required=True, description='Instance class'),
        'allocated_storage': fields.Integer(description='Storage in GB', default=20),
        'storage_type': fields.String(description='Storage type', default='gp2'),
        'multi_az': fields.Boolean(description='Multi-AZ deployment', default=False),
        'publicly_accessible': fields.Boolean(description='Publicly accessible', default=False),
        'backup_retention_period': fields.Integer(description='Backup retention days', default=7),
        'backup_window': fields.String(description='Backup window', default='03:00-04:00'),
        'maintenance_window': fields.String(description='Maintenance window', default='sun:04:00-sun:05:00'),
        'parameter_group': fields.String(description='Parameter group name'),
        'security_groups': fields.List(fields.String, description='Security group IDs'),
        'subnet_group': fields.String(description='Subnet group name'),
        'tags': fields.Raw(description='Database tags')
    })
    
    # Create resource request
    create_request = api.model('CreateResourceRequest', {
        'name': fields.String(required=True, description='Resource name'),
        'spec': fields.Raw(required=True, description='Resource specification'),
        'tenant_id': fields.String(description='Tenant ID (can be in header)')
    })
    
    # Update resource request
    update_request = api.model('UpdateResourceRequest', {
        'spec': fields.Raw(required=True, description='Updated resource specification'),
        'tenant_id': fields.String(description='Tenant ID (can be in header)')
    })
    
    # Status response
    status_response = api.model('StatusResponse', {
        'name': fields.String(required=True, description='Resource name'),
        'resource_type': fields.String(required=True, description='Resource type'),
        'status': fields.String(required=True, description='Current status'),
        'sync_status': fields.String(description='ArgoCD sync status'),
        'health_status': fields.String(description='ArgoCD health status'),
        'operation_state': fields.String(description='Operation state'),
        'last_sync': fields.DateTime(description='Last sync timestamp'),
        'resources': fields.Integer(description='Number of resources'),
        'created_at': fields.DateTime(required=True, description='Creation timestamp'),
        'updated_at': fields.DateTime(required=True, description='Last update timestamp')
    })
    
    # Error response
    error_response = api.model('ErrorResponse', {
        'error': fields.String(required=True, description='Error message'),
        'code': fields.String(description='Error code'),
        'details': fields.Raw(description='Error details')
    })
    
    return {
        'resource_model': resource_model,
        'namespace_spec': namespace_spec,
        'vm_spec': vm_spec,
        'app_spec': app_spec,
        'database_spec': database_spec,
        'create_request': create_request,
        'update_request': update_request,
        'status_response': status_response,
        'error_response': error_response
    }