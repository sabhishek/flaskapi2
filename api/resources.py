from flask import request, jsonify
from flask_restx import Resource, Namespace
from core.middleware import require_tenant
from resources import get_resource_manager, list_resource_types
from .models import create_api_models
import logging

logger = logging.getLogger(__name__)

def register_resources(api):
    """Register all resource endpoints"""
    
    # Create API models
    models = create_api_models(api)
    
    # Create namespace for each resource type
    for resource_type in list_resource_types():
        ns = Namespace(
            resource_type,
            description=f'{resource_type.title()} resource operations',
            path=f'/api/v1/{resource_type}'
        )
        
        # Register CRUD endpoints for this resource type
        register_crud_endpoints(ns, resource_type, models)
        api.add_namespace(ns)
    
    # Register generic status endpoint
    status_ns = Namespace(
        'status',
        description='Resource status operations',
        path='/api/v1/status'
    )
    register_status_endpoints(status_ns, models)
    api.add_namespace(status_ns)

def register_crud_endpoints(ns, resource_type, models):
    """Register CRUD endpoints for a resource type"""
    
    @ns.route('/create')
    class CreateResource(Resource):
        @ns.doc('create_resource')
        @ns.expect(models['create_request'])
        @ns.response(201, 'Resource created successfully', models['resource_model'])
        @ns.response(400, 'Invalid request', models['error_response'])
        @ns.response(409, 'Resource already exists', models['error_response'])
        @require_tenant
        def post(self):
            """Create a new resource"""
            try:
                data = request.get_json()
                name = data.get('name')
                spec = data.get('spec')
                
                if not name or not spec:
                    return {'error': 'Name and spec are required'}, 400
                
                manager = get_resource_manager(resource_type)
                result = manager.create_resource(name, spec)
                
                return result, 201
                
            except ValueError as e:
                return {'error': str(e)}, 400
            except Exception as e:
                logger.error(f"Failed to create {resource_type}: {e}")
                return {'error': 'Internal server error'}, 500
    
    @ns.route('/<string:name>')
    class ResourceDetail(Resource):
        @ns.doc('get_resource')
        @ns.response(200, 'Resource retrieved successfully', models['resource_model'])
        @ns.response(404, 'Resource not found', models['error_response'])
        @require_tenant
        def get(self, name):
            """Get a resource by name"""
            try:
                manager = get_resource_manager(resource_type)
                result = manager.get_resource(name)
                
                if not result:
                    return {'error': f'{resource_type.title()} not found'}, 404
                
                return result, 200
                
            except Exception as e:
                logger.error(f"Failed to get {resource_type}: {e}")
                return {'error': 'Internal server error'}, 500
        
        @ns.doc('update_resource')
        @ns.expect(models['update_request'])
        @ns.response(200, 'Resource updated successfully', models['resource_model'])
        @ns.response(404, 'Resource not found', models['error_response'])
        @require_tenant
        def put(self, name):
            """Update a resource"""
            try:
                data = request.get_json()
                spec = data.get('spec')
                
                if not spec:
                    return {'error': 'Spec is required'}, 400
                
                manager = get_resource_manager(resource_type)
                result = manager.update_resource(name, spec)
                
                return result, 200
                
            except ValueError as e:
                return {'error': str(e)}, 400
            except Exception as e:
                logger.error(f"Failed to update {resource_type}: {e}")
                return {'error': 'Internal server error'}, 500
        
        @ns.doc('delete_resource')
        @ns.response(204, 'Resource deleted successfully')
        @ns.response(404, 'Resource not found', models['error_response'])
        @require_tenant
        def delete(self, name):
            """Delete a resource"""
            try:
                manager = get_resource_manager(resource_type)
                result = manager.delete_resource(name)
                
                if not result:
                    return {'error': f'{resource_type.title()} not found'}, 404
                
                return '', 204
                
            except Exception as e:
                logger.error(f"Failed to delete {resource_type}: {e}")
                return {'error': 'Internal server error'}, 500
    
    @ns.route('/list')
    class ResourceList(Resource):
        @ns.doc('list_resources')
        @ns.response(200, 'Resources retrieved successfully', [models['resource_model']])
        @require_tenant
        def get(self):
            """List all resources"""
            try:
                manager = get_resource_manager(resource_type)
                results = manager.list_resources()
                
                return results, 200
                
            except Exception as e:
                logger.error(f"Failed to list {resource_type}: {e}")
                return {'error': 'Internal server error'}, 500

def register_status_endpoints(ns, models):
    """Register status endpoints"""
    
    @ns.route('/<string:resource_type>/<string:name>')
    class ResourceStatus(Resource):
        @ns.doc('get_resource_status')
        @ns.response(200, 'Status retrieved successfully', models['status_response'])
        @ns.response(404, 'Resource not found', models['error_response'])
        @require_tenant
        def get(self, resource_type, name):
            """Get resource status"""
            try:
                if resource_type not in list_resource_types():
                    return {'error': f'Unknown resource type: {resource_type}'}, 400
                
                manager = get_resource_manager(resource_type)
                result = manager.get_status(name)
                
                return result, 200
                
            except ValueError as e:
                return {'error': str(e)}, 404
            except Exception as e:
                logger.error(f"Failed to get status for {resource_type}/{name}: {e}")
                return {'error': 'Internal server error'}, 500