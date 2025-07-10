from typing import Dict
from core.resource_manager import ResourceManager
from core.template_engine import TemplateEngine
import logging

logger = logging.getLogger(__name__)

class AppManager(ResourceManager):
    """Manager for Application deployment resources"""
    
    def __init__(self):
        super().__init__('app')
        self.template_engine = TemplateEngine()
    
    def validate_spec(self, spec: Dict) -> bool:
        """Validate application specification"""
        required_fields = ['name', 'image', 'port']
        
        for field in required_fields:
            if field not in spec:
                logger.error(f"Missing required field: {field}")
                return False
        
        # Validate port
        port = spec.get('port')
        if not isinstance(port, int) or port < 1 or port > 65535:
            logger.error("Port must be between 1 and 65535")
            return False
        
        # Validate replicas
        replicas = spec.get('replicas', 1)
        if not isinstance(replicas, int) or replicas < 1 or replicas > 10:
            logger.error("Replicas must be between 1 and 10")
            return False
        
        return True
    
    def generate_manifest(self, name: str, spec: Dict, tenant_id: str) -> str:
        """Generate Kubernetes application manifests"""
        try:
            template_name = 'app.yaml'
            
            context = {
                'name': spec.get('name', name),
                'tenant_id': tenant_id,
                'namespace': f"{tenant_id}-apps",
                'image': spec.get('image'),
                'port': spec.get('port'),
                'replicas': spec.get('replicas', 1),
                'env_vars': spec.get('env_vars', {}),
                'resources': spec.get('resources', {}),
                'labels': spec.get('labels', {}),
                'annotations': spec.get('annotations', {}),
                'service_type': spec.get('service_type', 'ClusterIP'),
                'ingress': spec.get('ingress', {}),
                'health_check': spec.get('health_check', {})
            }
            
            # Add tenant-specific labels
            context['labels'].update({
                'tenant.io/id': tenant_id,
                'managed-by': 'gitops-api',
                'app.kubernetes.io/name': context['name']
            })
            
            try:
                return self.template_engine.render_template(template_name, **context)
            except Exception:
                return self._generate_inline_manifest(context)
                
        except Exception as e:
            logger.error(f"Failed to generate app manifest: {e}")
            raise
    
    def _generate_inline_manifest(self, context: Dict) -> str:
        """Generate manifest using inline template"""
        template_str = """apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ name }}
  namespace: {{ namespace }}
  labels:
{% for key, value in labels.items() %}
    {{ key }}: "{{ value }}"
{% endfor %}
  annotations:
{% for key, value in annotations.items() %}
    {{ key }}: "{{ value }}"
{% endfor %}
spec:
  replicas: {{ replicas }}
  selector:
    matchLabels:
      app: {{ name }}
  template:
    metadata:
      labels:
        app: {{ name }}
{% for key, value in labels.items() %}
        {{ key }}: "{{ value }}"
{% endfor %}
    spec:
      containers:
      - name: {{ name }}
        image: {{ image }}
        ports:
        - containerPort: {{ port }}
        {% if env_vars %}
        env:
        {% for key, value in env_vars.items() %}
        - name: {{ key }}
          value: "{{ value }}"
        {% endfor %}
        {% endif %}
        {% if resources %}
        resources:
          {% if resources.requests %}
          requests:
          {% for key, value in resources.requests.items() %}
            {{ key }}: "{{ value }}"
          {% endfor %}
          {% endif %}
          {% if resources.limits %}
          limits:
          {% for key, value in resources.limits.items() %}
            {{ key }}: "{{ value }}"
          {% endfor %}
          {% endif %}
        {% endif %}
        {% if health_check %}
        {% if health_check.liveness %}
        livenessProbe:
          httpGet:
            path: {{ health_check.liveness.path | default('/health') }}
            port: {{ port }}
          initialDelaySeconds: {{ health_check.liveness.initial_delay | default(30) }}
          periodSeconds: {{ health_check.liveness.period | default(10) }}
        {% endif %}
        {% if health_check.readiness %}
        readinessProbe:
          httpGet:
            path: {{ health_check.readiness.path | default('/ready') }}
            port: {{ port }}
          initialDelaySeconds: {{ health_check.readiness.initial_delay | default(5) }}
          periodSeconds: {{ health_check.readiness.period | default(5) }}
        {% endif %}
        {% endif %}
---
apiVersion: v1
kind: Service
metadata:
  name: {{ name }}-service
  namespace: {{ namespace }}
  labels:
{% for key, value in labels.items() %}
    {{ key }}: "{{ value }}"
{% endfor %}
spec:
  selector:
    app: {{ name }}
  ports:
  - port: {{ port }}
    targetPort: {{ port }}
  type: {{ service_type }}
{% if ingress %}
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {{ name }}-ingress
  namespace: {{ namespace }}
  labels:
{% for key, value in labels.items() %}
    {{ key }}: "{{ value }}"
{% endfor %}
  {% if ingress.annotations %}
  annotations:
  {% for key, value in ingress.annotations.items() %}
    {{ key }}: "{{ value }}"
  {% endfor %}
  {% endif %}
spec:
  {% if ingress.tls %}
  tls:
  {% for tls_config in ingress.tls %}
  - hosts:
    {% for host in tls_config.hosts %}
    - {{ host }}
    {% endfor %}
    secretName: {{ tls_config.secret_name }}
  {% endfor %}
  {% endif %}
  rules:
  {% for rule in ingress.rules %}
  - host: {{ rule.host }}
    http:
      paths:
      - path: {{ rule.path | default('/') }}
        pathType: {{ rule.path_type | default('Prefix') }}
        backend:
          service:
            name: {{ name }}-service
            port:
              number: {{ port }}
  {% endfor %}
{% endif %}
"""
        return self.template_engine.render_from_string(template_str, **context)