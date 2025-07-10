from flask import request, jsonify, g
from functools import wraps
import logging

logger = logging.getLogger(__name__)

class TenantMiddleware:
    """Middleware to handle tenant awareness"""
    
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app
    
    def __call__(self, environ, start_response):
        def new_start_response(status, headers):
            return start_response(status, headers)
        
        # Extract tenant from request before processing
        self.extract_tenant_info(environ)
        
        return self.wsgi_app(environ, new_start_response)
    
    def extract_tenant_info(self, environ):
        """Extract tenant information from request"""
        # This will be available in Flask's request context
        pass

def require_tenant(f):
    """Decorator to ensure tenant is present in request"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        tenant_id = get_tenant_id()
        if not tenant_id:
            return jsonify({'error': 'Tenant ID is required'}), 400
        
        g.tenant_id = tenant_id
        return f(*args, **kwargs)
    return decorated_function

def get_tenant_id():
    """Extract tenant ID from request headers or JSON body"""
    from flask import current_app
    
    tenant_header = current_app.config.get('TENANT_HEADER', 'X-Tenant-ID')
    
    # Try to get from headers first
    tenant_id = request.headers.get(tenant_header)
    
    # If not in headers, try JSON body
    if not tenant_id and request.is_json:
        tenant_id = request.json.get('tenant_id')
    
    # Try query parameters as fallback
    if not tenant_id:
        tenant_id = request.args.get('tenant_id')
    
    return tenant_id

def get_current_tenant():
    """Get current tenant from Flask's g object"""
    return getattr(g, 'tenant_id', None)