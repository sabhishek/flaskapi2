from flask_restx import fields
from flask_restx.namespace import Namespace

# API models for request/response serialization
def create_api_models(api):
    """Create API models for OpenAPI documentation"""
    
    # Job response model
    job_response = api.model('JobResponse', {
        'job_id': fields.String(required=True, description='Job ID'),
        'status': fields.String(required=True, description='Job status'),
        'message': fields.String(description='Status message')
    })
    
    # Create resource request
    create_request = api.model('CreateResourceRequest', {
        'name': fields.String(required=True, description='Resource name'),
        'flavor': fields.String(description='Resource flavor (small/medium/large/custom)', default='custom'),
        'spec': fields.Raw(description='Resource specification'),
        'tenant_id': fields.String(description='Tenant ID (can be in header)'),
        'cluster_id': fields.String(description='Cluster ID (can be in header)')
    })
    
    # Update resource request
    update_request = api.model('UpdateResourceRequest', {
        'name': fields.String(required=True, description='Resource name'),
        'flavor': fields.String(description='Resource flavor'),
        'spec': fields.Raw(description='Updated resource specification'),
        'tenant_id': fields.String(description='Tenant ID (can be in header)'),
        'cluster_id': fields.String(description='Cluster ID (can be in header)')
    })
    
    # Delete resource request
    delete_request = api.model('DeleteResourceRequest', {
        'name': fields.String(required=True, description='Resource name'),
        'tenant_id': fields.String(description='Tenant ID (can be in header)'),
        'cluster_id': fields.String(description='Cluster ID (can be in header)')
    })
    
    # Status response
    status_response = api.model('StatusResponse', {
        'job_id': fields.String(required=True, description='Job ID'),
        'job_type': fields.String(required=True, description='Job type'),
        'tenant_id': fields.String(required=True, description='Tenant ID'),
        'cluster_id': fields.String(description='Cluster ID'),
        'resource_type': fields.String(required=True, description='Resource type'),
        'resource_name': fields.String(required=True, description='Resource name'),
        'operation': fields.String(required=True, description='Operation'),
        'status': fields.String(required=True, description='Current status'),
        'created_at': fields.DateTime(required=True, description='Creation timestamp'),
        'updated_at': fields.DateTime(required=True, description='Last update timestamp'),
        'logs': fields.List(fields.String, description='Job logs'),
        'metadata': fields.Raw(description='Job metadata')
    })
    
    # Error response
    error_response = api.model('ErrorResponse', {
        'error': fields.String(required=True, description='Error message'),
        'code': fields.String(description='Error code'),
        'details': fields.Raw(description='Error details')
    })
    
    # Namespace specification
    namespace_spec = api.model('NamespaceSpec', {
        'labels': fields.Raw(description='Namespace labels'),
        'annotations': fields.Raw(description='Namespace annotations'),
        'resource_quota': fields.Raw(description='Resource quota settings'),
        'network_policies': fields.List(fields.Raw, description='Network policies')
    })
    
    # VM specification
    vm_spec = api.model('VMSpec', {
        'instance_type': fields.String(description='VM instance type'),
        'image': fields.String(description='VM image'),
        'disk_size': fields.Integer(description='Disk size in GB'),
        'network_config': fields.Raw(description='Network configuration'),
        'tags': fields.Raw(description='VM tags'),
        'user_data': fields.String(description='User data script')
    })
    
    # OS Image specification
    osimage_spec = api.model('OSImageSpec', {
        'base_image': fields.String(description='Base image'),
        'packages': fields.List(fields.String, description='Packages to install'),
        'scripts': fields.List(fields.String, description='Setup scripts'),
        'tags': fields.Raw(description='Image tags')
    })
    
    # Misc infrastructure specification
    misc_spec = api.model('MiscSpec', {
        'type': fields.String(description='Infrastructure type (dns, cert, secret)'),
        'config': fields.Raw(description='Type-specific configuration')
    })
    
    return {
        'job_response': job_response,
        'create_request': create_request,
        'update_request': update_request,
        'delete_request': delete_request,
        'status_response': status_response,
        'error_response': error_response,
        'namespace_spec': namespace_spec,
        'vm_spec': vm_spec,
        'osimage_spec': osimage_spec,
        'misc_spec': misc_spec
    }