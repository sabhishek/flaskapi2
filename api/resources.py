from flask import request, jsonify
from flask_restx import Resource, Namespace
from core.middleware import require_tenant, get_current_tenant, get_current_cluster
from core.resource_config import ResourceConfigManager
from core.job_manager import JobManager
from core.git_manager import GitManager
from core.template_engine import TemplateEngine
from core.webhook_manager import WebhookManager
from .models import create_api_models
import logging

logger = logging.getLogger(__name__)

def register_resources(api):
    """Register all resource endpoints"""
    
    # Create API models
    models = create_api_models(api)
    
    # Initialize managers
    config_manager = ResourceConfigManager()
    
    # Create namespace for each resource type
    for resource_type in config_manager.list_resource_types():
        ns = Namespace(
            resource_type,
            description=f'{resource_type.title()} resource operations',
            path=f'/api/v1/{resource_type}'
        )
        
        # Register CRUD endpoints for this resource type
        register_crud_endpoints(ns, resource_type, models, config_manager)
        api.add_namespace(ns)
    
    # Register status endpoint
    status_ns = Namespace(
        'status',
        description='Job status operations',
        path='/api/v1/status'
    )
    register_status_endpoints(status_ns, models)
    api.add_namespace(status_ns)
    
    # Register tenant endpoints
    tenant_ns = Namespace(
        'tenant',
        description='Tenant operations',
        path='/api/v1/tenant'
    )
    register_tenant_endpoints(tenant_ns, models)
    api.add_namespace(tenant_ns)

def register_crud_endpoints(ns, resource_type, models, config_manager):
    """Register CRUD endpoints for a resource type"""
    
    @ns.route('/create')
    class CreateResource(Resource):
        @ns.doc('create_resource')
        @ns.expect(models['create_request'])
        @ns.response(202, 'Job submitted successfully', models['job_response'])
        @ns.response(400, 'Invalid request', models['error_response'])
        @require_tenant
        def post(self):
            """Create a new resource (async)"""
            try:
                from flask import current_app
                
                data = request.get_json()
                name = data.get('name')
                flavor = data.get('flavor', 'custom')
                spec = data.get('spec', {})
                
                if not name:
                    return {'error': 'Name is required'}, 400
                
                tenant_id = get_current_tenant()
                cluster_id = get_current_cluster()
                
                # Get resource configuration
                resource_config = config_manager.get_resource_config(resource_type)
                if not resource_config:
                    return {'error': f'Unknown resource type: {resource_type}'}, 400
                
                # Submit async job
                job_manager = current_app.job_manager
                job_id = job_manager.submit_job(
                    job_type='create',
                    tenant_id=tenant_id,
                    cluster_id=cluster_id,
                    resource_type=resource_type,
                    resource_name=name,
                    operation='create',
                    spec={'flavor': flavor, **spec}
                )
                
                return {
                    'job_id': job_id,
                    'status': 'submitted',
                    'message': f'{resource_type.title()} creation job submitted'
                }, 202
                
            except Exception as e:
                logger.error(f"Failed to create {resource_type}: {e}")
                return {'error': 'Internal server error'}, 500
    
    @ns.route('/update')
    class UpdateResource(Resource):
        @ns.doc('update_resource')
        @ns.expect(models['update_request'])
        @ns.response(202, 'Job submitted successfully', models['job_response'])
        @ns.response(400, 'Invalid request', models['error_response'])
        @require_tenant
        def put(self):
            """Update a resource (async)"""
            try:
                from flask import current_app
                
                data = request.get_json()
                name = data.get('name')
                flavor = data.get('flavor')
                spec = data.get('spec', {})
                
                if not name:
                    return {'error': 'Name is required'}, 400
                
                tenant_id = get_current_tenant()
                cluster_id = get_current_cluster()
                
                # Submit async job
                job_manager = current_app.job_manager
                job_id = job_manager.submit_job(
                    job_type='update',
                    tenant_id=tenant_id,
                    cluster_id=cluster_id,
                    resource_type=resource_type,
                    resource_name=name,
                    operation='update',
                    spec={'flavor': flavor, **spec}
                )
                
                return {
                    'job_id': job_id,
                    'status': 'submitted',
                    'message': f'{resource_type.title()} update job submitted'
                }, 202
                
            except Exception as e:
                logger.error(f"Failed to update {resource_type}: {e}")
                return {'error': 'Internal server error'}, 500
    
    @ns.route('/delete')
    class DeleteResource(Resource):
        @ns.doc('delete_resource')
        @ns.expect(models['delete_request'])
        @ns.response(202, 'Job submitted successfully', models['job_response'])
        @ns.response(400, 'Invalid request', models['error_response'])
        @require_tenant
        def delete(self):
            """Delete a resource (async)"""
            try:
                from flask import current_app
                
                data = request.get_json()
                name = data.get('name')
                
                if not name:
                    return {'error': 'Name is required'}, 400
                
                tenant_id = get_current_tenant()
                cluster_id = get_current_cluster()
                
                # Submit async job
                job_manager = current_app.job_manager
                job_id = job_manager.submit_job(
                    job_type='delete',
                    tenant_id=tenant_id,
                    cluster_id=cluster_id,
                    resource_type=resource_type,
                    resource_name=name,
                    operation='delete'
                )
                
                return {
                    'job_id': job_id,
                    'status': 'submitted',
                    'message': f'{resource_type.title()} deletion job submitted'
                }, 202
                
            except Exception as e:
                logger.error(f"Failed to delete {resource_type}: {e}")
                return {'error': 'Internal server error'}, 500
    
    @ns.route('/list')
    class ListResources(Resource):
        @ns.doc('list_resources')
        @ns.response(202, 'Job submitted successfully', models['job_response'])
        @require_tenant
        def get(self):
            """List all resources (async)"""
            try:
                from flask import current_app
                
                tenant_id = get_current_tenant()
                cluster_id = get_current_cluster()
                
                # Submit async job
                job_manager = current_app.job_manager
                job_id = job_manager.submit_job(
                    job_type='list',
                    tenant_id=tenant_id,
                    cluster_id=cluster_id,
                    resource_type=resource_type,
                    resource_name='*',
                    operation='list'
                )
                
                return {
                    'job_id': job_id,
                    'status': 'submitted',
                    'message': f'{resource_type.title()} list job submitted'
                }, 202
                
            except Exception as e:
                logger.error(f"Failed to list {resource_type}: {e}")
                return {'error': 'Internal server error'}, 500

def register_status_endpoints(ns, models):
    """Register status endpoints"""
    
    @ns.route('/<string:job_id>')
    class JobStatus(Resource):
        @ns.doc('get_job_status')
        @ns.response(200, 'Status retrieved successfully', models['status_response'])
        @ns.response(404, 'Job not found', models['error_response'])
        def get(self, job_id):
            """Get job status"""
            try:
                from flask import current_app
                
                job_manager = current_app.job_manager
                job_status = job_manager.get_job_status(job_id)
                
                if not job_status:
                    return {'error': 'Job not found'}, 404
                
                return job_status, 200
                
            except Exception as e:
                logger.error(f"Failed to get job status: {e}")
                return {'error': 'Internal server error'}, 500

def register_tenant_endpoints(ns, models):
    """Register tenant endpoints"""
    
    @ns.route('/<string:tenant_id>/metrics')
    class TenantMetrics(Resource):
        @ns.doc('get_tenant_metrics')
        @ns.response(200, 'Metrics retrieved successfully')
        def get(self, tenant_id):
            """Get tenant metrics"""
            # Implementation for tenant metrics
            return {
                'tenant_id': tenant_id,
                'total_resources': 0,
                'active_jobs': 0,
                'failed_jobs': 0,
                'last_activity': None
            }, 200
    
    @ns.route('/<string:tenant_id>/resources')
    class TenantResources(Resource):
        @ns.doc('get_tenant_resources')
        @ns.response(200, 'Resources retrieved successfully')
        def get(self, tenant_id):
            """Get tenant resources"""
            # Implementation for tenant resource inventory
            return {
                'tenant_id': tenant_id,
                'resources': {}
            }, 200