# GitOps Infrastructure API

A Flask-based extensible API with OpenAPI specification that supports tenant-aware CRUD operations for infrastructure resources via GitOps (ArgoCD + Crossplane).

## Features

- **Tenant-aware CRUD operations** for infrastructure resources
- **OpenAPI 3.0 specification** with Swagger UI
- **GitOps workflow** using ArgoCD and Git repositories
- **Extensible architecture** for adding new resource types
- **Template-based manifest generation** using Jinja2
- **Status monitoring** via ArgoCD API integration
- **Multi-tenant resource isolation**

## Supported Resources

- **Namespace**: Kubernetes namespaces with resource quotas and network policies
- **VM**: Virtual machines via Crossplane (AWS EC2)
- **App**: Application deployments with services and ingress
- **Database**: RDS databases via Crossplane

## Quick Start

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Set up environment variables**:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Initialize database**:
```bash
python migrations/create_tables.py
```

4. **Run the application**:
```bash
python app.py
```

5. **Access the API**:
   - API: http://localhost:5000/api/v1
   - Swagger UI: http://localhost:5000/docs

## API Endpoints

### Generic CRUD Pattern

All resources follow the same CRUD pattern:

- `POST /api/v1/{resource}/create` - Create resource
- `GET /api/v1/{resource}/{name}` - Get resource
- `PUT /api/v1/{resource}/{name}` - Update resource
- `DELETE /api/v1/{resource}/{name}` - Delete resource
- `GET /api/v1/{resource}/list` - List all resources

### Status Endpoints

- `GET /api/v1/status/{resource}/{name}` - Get resource status from ArgoCD

## Usage Examples

### Create a Namespace

```bash
curl -X POST http://localhost:5000/api/v1/namespace/create \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: tenant-001" \
  -d '{
    "name": "my-namespace",
    "spec": {
      "name": "my-namespace",
      "labels": {
        "environment": "development"
      },
      "resource_quota": {
        "requests.cpu": "2",
        "requests.memory": "4Gi",
        "limits.cpu": "4",
        "limits.memory": "8Gi"
      }
    }
  }'
```

### Deploy an Application

```bash
curl -X POST http://localhost:5000/api/v1/app/create \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: tenant-001" \
  -d '{
    "name": "my-app",
    "spec": {
      "name": "my-app",
      "image": "nginx:latest",
      "port": 80,
      "replicas": 3,
      "service_type": "LoadBalancer",
      "env_vars": {
        "ENV": "production"
      }
    }
  }'
```

### Create a Virtual Machine

```bash
curl -X POST http://localhost:5000/api/v1/vm/create \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: tenant-001" \
  -d '{
    "name": "my-vm",
    "spec": {
      "name": "my-vm",
      "instance_type": "t3.medium",
      "image": "ami-0abcdef1234567890",
      "disk_size": 50,
      "key_name": "my-key-pair",
      "security_groups": ["sg-12345678"],
      "tags": {
        "Environment": "production"
      }
    }
  }'
```

### Check Resource Status

```bash
curl -X GET http://localhost:5000/api/v1/status/app/my-app \
  -H "X-Tenant-ID: tenant-001"
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Flask secret key | `dev-secret-key` |
| `DATABASE_URL` | Database connection string | `sqlite:///app.db` |
| `GIT_REPO_URL` | Git repository URL | - |
| `GIT_BRANCH` | Git branch | `main` |
| `GIT_USERNAME` | Git username | - |
| `GIT_PASSWORD` | Git password/token | - |
| `ARGOCD_URL` | ArgoCD server URL | - |
| `ARGOCD_USERNAME` | ArgoCD username | - |
| `ARGOCD_PASSWORD` | ArgoCD password | - |
| `ARGOCD_TOKEN` | ArgoCD token (alternative to username/password) | - |
| `TEMPLATES_DIR` | Templates directory | `templates` |
| `MANIFESTS_DIR` | Manifests directory in Git | `manifests` |
| `TENANT_HEADER` | Tenant ID header name | `X-Tenant-ID` |
| `REQUIRE_TENANT` | Require tenant ID | `true` |

## Architecture

### Components

1. **Flask App** (`app.py`): Main application with Flask-RESTX
2. **Resource Managers** (`resources/`): Pluggable resource handlers
3. **GitOps Manager** (`core/gitops.py`): Git operations
4. **ArgoCD Client** (`core/argocd.py`): ArgoCD API integration
5. **Template Engine** (`core/template_engine.py`): Jinja2 templating
6. **Database Models** (`core/database.py`): SQLAlchemy models
7. **Middleware** (`core/middleware.py`): Tenant awareness

### Workflow

1. **API Request**: Client sends CRUD request with tenant ID
2. **Validation**: Request is validated and tenant is extracted
3. **Resource Processing**: Appropriate resource manager processes request
4. **Manifest Generation**: Jinja2 templates generate Kubernetes manifests
5. **Git Operations**: Manifests are committed to tenant-specific folders
6. **ArgoCD Sync**: ArgoCD applications are created/updated
7. **Status Tracking**: Resource status is tracked in database

## Extending the API

### Adding New Resource Types

1. Create a new resource manager in `resources/`:

```python
from core.resource_manager import ResourceManager
from core.template_engine import TemplateEngine

class MyResourceManager(ResourceManager):
    def __init__(self):
        super().__init__('myresource')
        self.template_engine = TemplateEngine()
    
    def validate_spec(self, spec):
        # Implement validation logic
        return True
    
    def generate_manifest(self, name, spec, tenant_id):
        # Implement manifest generation
        return self.template_engine.render_template('myresource.yaml', **context)
```

2. Register the new resource manager in `resources/__init__.py`:

```python
from .myresource import MyResourceManager

RESOURCE_MANAGERS = {
    # ... existing managers
    'myresource': MyResourceManager
}
```

3. Create a template file in `templates/myresource.yaml`

4. The new resource will automatically be available at `/api/v1/myresource/*`

## Security

- **Tenant Isolation**: All resources are isolated by tenant ID
- **Input Validation**: All inputs are validated before processing
- **Database Security**: Prepared statements prevent SQL injection
- **Git Security**: Secure authentication with Git repositories
- **ArgoCD Security**: Token-based authentication with ArgoCD

## Testing

Run tests with:

```bash
pip install -r requirements-dev.txt
pytest tests/
```

## Production Deployment

1. **Use PostgreSQL**: Set `DATABASE_URL` to PostgreSQL connection string
2. **Configure WSGI**: Use gunicorn or similar WSGI server
3. **Environment Variables**: Set all required environment variables
4. **Database Migration**: Run database migrations
5. **Monitoring**: Set up logging and monitoring

Example production command:
```bash
gunicorn --bind 0.0.0.0:5000 --workers 4 app:app
```

## License

MIT License