# GitOps Infrastructure API v2.0

A Flask-based REST API that enables declarative infrastructure provisioning and lifecycle management via Git. This system is agnostic to how manifests are applied — it simply creates, updates, deletes, and reads YAML/HCL templates in dedicated Git repositories.

## 🧱 Architecture Overview

- **Git-First**: All infrastructure definitions stored in dedicated Git repositories
- **Async Processing**: All operations return job IDs for async tracking
- **Multi-Tenant**: Tenant and cluster-aware resource isolation
- **Extensible**: Dynamic resource type configuration
- **Webhook Support**: Configurable callbacks for external integrations
- **Development Mode**: In-memory processing without PostgreSQL/Redis dependencies

## ✅ Core Features

### 1. REST API for Infrastructure Resource Lifecycle

Support full CRUDL (Create, Read, Update, Delete, List) for each resource type:

- **Namespace** (OCP project)
- **VMs** 
- **OS Images** (e.g., Packer builds)
- **Misc Infrastructure** (e.g., DNS, secrets, certificates)

All operations are asynchronous and return a `job_id`:

```bash
# Create a namespace
curl -X POST http://localhost:5000/api/v1/namespace/create \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: tenant1" \
  -H "X-Cluster-ID: cluster-a" \
  -d '{
    "name": "dev-namespace",
    "flavor": "small",
    "spec": {
      "labels": {"environment": "development"}
    }
  }'

# Response
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "submitted",
  "message": "Namespace creation job submitted"
}

# Check job status
curl -X GET http://localhost:5000/api/v1/status/550e8400-e29b-41d4-a716-446655440000
```

### 2. Git Repositories as Source of Truth

Each resource type has its dedicated Git repository with tenant/cluster organization:

```
📁 ocp-resources-gitops/
└── tenants/
    └── tenant1/
        └── cluster-a/
            ├── namespace/
            │   └── dev-namespace/manifest.yaml
            ├── pvs/
            └── quota/

📁 vm-resources-gitops/
└── tenants/
    └── tenant1/
        └── dev-vm/manifest.yaml

📁 os-image-builds-gitops/
└── tenants/
    └── tenant1/
        └── ubuntu-small.pkr.hcl

📁 misc-infra-gitops/
└── tenants/
    └── tenant1/
        ├── certs/
        ├── dns/
        └── secrets/
```

### 3. Central Template Repository

Reusable templates with flavor support:

```
📁 infra-templates/
├── namespaces/
│   ├── small.yaml.j2
│   ├── medium.yaml.j2
│   └── custom.yaml.j2
├── vms/
│   ├── small.yaml.j2
│   └── large.yaml.j2
├── osimage/
│   ├── ubuntu-small.pkr.hcl.j2
│   └── rhel-custom.pkr.hcl.j2
└── misc/
    └── dns-record.yaml.j2
```

### 4. Async Job Engine with Webhook Support

- All operations return `job_id` for tracking
- Configurable webhook callbacks per resource type
- Support for single or staged notifications

## 🚀 Quick Start

### Development Mode (No Database Required)

1. **Install dependencies**:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

2. **Set up environment**:
```bash
cp .env.example .env
# Edit .env and set DEV_MODE=true
```

3. **Run the application**:
```bash
python app.py
```

4. **Access the API**:
   - API: http://localhost:5000/api/v1
   - Swagger UI: http://localhost:5000/docs

### Production Mode

1. **Set up PostgreSQL and Redis**:
```bash
# PostgreSQL for job storage
# Redis for Celery task queue
```

2. **Configure environment**:
```bash
cp .env.example .env
# Set DEV_MODE=false
# Configure DATABASE_URL and REDIS_URL
```

3. **Initialize database**:
```bash
python migrations/create_tables.py
```

4. **Start Celery worker**:
```bash
celery -A app.celery worker --loglevel=info
```

5. **Run the application**:
```bash
gunicorn --bind 0.0.0.0:5000 --workers 4 app:app
```

## 📋 API Examples

### Create a VM

```bash
curl -X POST http://localhost:5000/api/v1/vm/create \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: tenant1" \
  -d '{
    "name": "web-server",
    "flavor": "medium",
    "spec": {
      "instance_type": "t3.medium",
      "tags": {"purpose": "web"}
    }
  }'
```

### Create an OS Image

```bash
curl -X POST http://localhost:5000/api/v1/osimage/create \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: tenant1" \
  -d '{
    "name": "custom-ubuntu",
    "flavor": "ubuntu-small",
    "spec": {
      "packages": ["nginx", "docker"],
      "scripts": ["setup-monitoring.sh"]
    }
  }'
```

### Update a Resource

```bash
curl -X PUT http://localhost:5000/api/v1/namespace/update \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: tenant1" \
  -H "X-Cluster-ID: cluster-a" \
  -d '{
    "name": "dev-namespace",
    "spec": {
      "labels": {"environment": "staging"}
    }
  }'
```

### Check Job Status

```bash
curl -X GET http://localhost:5000/api/v1/status/{job_id}

# Response
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "tenant_id": "tenant1",
  "resource_type": "namespace",
  "resource_name": "dev-namespace",
  "operation": "create",
  "logs": [
    "Job started",
    "Template rendered",
    "Manifest committed to Git",
    "Webhook notification sent"
  ],
  "metadata": {
    "git_commit": "abc123",
    "webhook_status": "sent"
  }
}
```

## 🔧 Configuration

### Resource Type Configuration

Resource types are dynamically configured. Example configuration:

```python
resource_types = {
    'namespace': {
        'repo_url': 'https://github.com/org/ocp-resources-gitops.git',
        'template_dir': 'namespaces/',
        'cluster_aware': True,
        'webhook': {
            'enabled': True,
            'url': 'https://webhook.example.com/namespace',
            'mode': 'single'
        },
        'flavors': ['small', 'medium', 'large', 'custom']
    }
}
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DEV_MODE` | Enable development mode | `false` |
| `DATABASE_URL` | PostgreSQL connection string | - |
| `REDIS_URL` | Redis connection string | - |
| `TEMPLATE_REPO_URL` | Template repository URL | - |
| `GIT_USERNAME` | Git username | - |
| `GIT_PASSWORD` | Git password/token | - |
| `TENANT_HEADER` | Tenant ID header name | `X-Tenant-ID` |
| `CLUSTER_HEADER` | Cluster ID header name | `X-Cluster-ID` |

## 🧪 Development Features

- **In-memory job tracking**: No database required
- **Simulated webhooks**: Logs webhook payloads instead of sending
- **Mock Git operations**: Can work without actual Git repositories
- **Fast iteration**: Immediate feedback for development

## 🔌 Extensibility

### Adding New Resource Types

1. **Add configuration**:
```python
config_manager.add_resource_type(ResourceTypeConfig(
    name='loadbalancer',
    repo_url='https://github.com/org/lb-gitops.git',
    template_dir='loadbalancers/',
    cluster_aware=True,
    flavors=['small', 'large']
))
```

2. **Create templates**:
```bash
# Add templates to infra-templates repo
mkdir loadbalancers/
echo "template content" > loadbalancers/small.yaml.j2
```

3. **Configure webhooks** (optional):
```python
webhook=WebhookConfig(
    enabled=True,
    url='https://webhook.example.com/loadbalancer',
    mode='staged'
)
```

The new resource type is automatically available at `/api/v1/loadbalancer/*`

## 📊 Monitoring

### Tenant Metrics

```bash
curl -X GET http://localhost:5000/api/v1/tenant/tenant1/metrics
```

### Tenant Resources

```bash
curl -X GET http://localhost:5000/api/v1/tenant/tenant1/resources
```

## 🔒 Security

- **Tenant Isolation**: All resources are isolated by tenant ID
- **Input Validation**: All inputs are validated before processing
- **Git Security**: Secure authentication with Git repositories
- **Webhook Security**: Configurable timeouts and retries

## 📦 Deployment

### Docker

```dockerfile
FROM python:3.11-slim
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gitops-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: gitops-api
  template:
    metadata:
      labels:
        app: gitops-api
    spec:
      containers:
      - name: api
        image: gitops-api:latest
        env:
        - name: DEV_MODE
          value: "false"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
```

## 📝 License

MIT License