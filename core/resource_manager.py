from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from core.database import db, Resource, ResourceOperation
from core.middleware import get_current_tenant
from core.gitops import GitOpsManager
from core.argocd import ArgoCDClient
import logging

logger = logging.getLogger(__name__)

class ResourceManager(ABC):
    """Abstract base class for resource managers"""
    
    def __init__(self, resource_type: str):
        self.resource_type = resource_type
        self.gitops = GitOpsManager()
        self.argocd = ArgoCDClient()
    
    @abstractmethod
    def validate_spec(self, spec: Dict) -> bool:
        """Validate resource specification"""
        pass
    
    @abstractmethod
    def generate_manifest(self, name: str, spec: Dict, tenant_id: str) -> str:
        """Generate Kubernetes manifest from spec"""
        pass
    
    def create_resource(self, name: str, spec: Dict) -> Dict:
        """Create a new resource"""
        tenant_id = get_current_tenant()
        
        # Validate input
        if not self.validate_spec(spec):
            raise ValueError(f"Invalid spec for {self.resource_type}")
        
        # Check if resource already exists
        existing = Resource.query.filter_by(
            tenant_id=tenant_id,
            name=name,
            resource_type=self.resource_type
        ).first()
        
        if existing:
            raise ValueError(f"Resource {name} already exists")
        
        # Create resource record
        resource = Resource(
            tenant_id=tenant_id,
            name=name,
            resource_type=self.resource_type,
            spec=spec,
            status='creating'
        )
        
        db.session.add(resource)
        db.session.commit()
        
        # Generate and deploy manifest
        try:
            manifest = self.generate_manifest(name, spec, tenant_id)
            manifest_path = self.gitops.deploy_manifest(
                tenant_id, self.resource_type, name, manifest
            )
            
            # Update resource with manifest path
            resource.manifest_path = manifest_path
            resource.argocd_app_name = f"{tenant_id}-{self.resource_type}-{name}"
            
            # Create ArgoCD application
            self.argocd.create_application(
                resource.argocd_app_name,
                tenant_id,
                self.resource_type
            )
            
            # Log operation
            operation = ResourceOperation(
                resource_id=resource.id,
                tenant_id=tenant_id,
                operation='create',
                status='success',
                details={'manifest_path': manifest_path}
            )
            
            db.session.add(operation)
            resource.status = 'syncing'
            db.session.commit()
            
            return resource.to_dict()
            
        except Exception as e:
            logger.error(f"Failed to create resource {name}: {str(e)}")
            resource.status = 'failed'
            
            operation = ResourceOperation(
                resource_id=resource.id,
                tenant_id=tenant_id,
                operation='create',
                status='failed',
                error_message=str(e)
            )
            
            db.session.add(operation)
            db.session.commit()
            raise
    
    def get_resource(self, name: str) -> Optional[Dict]:
        """Get a resource by name"""
        tenant_id = get_current_tenant()
        
        resource = Resource.query.filter_by(
            tenant_id=tenant_id,
            name=name,
            resource_type=self.resource_type
        ).first()
        
        if not resource:
            return None
        
        # Get current status from ArgoCD
        if resource.argocd_app_name:
            argocd_status = self.argocd.get_application_status(resource.argocd_app_name)
            if argocd_status:
                resource.status = argocd_status.get('status', resource.status)
        
        return resource.to_dict()
    
    def list_resources(self) -> List[Dict]:
        """List all resources for current tenant"""
        tenant_id = get_current_tenant()
        
        resources = Resource.query.filter_by(
            tenant_id=tenant_id,
            resource_type=self.resource_type
        ).all()
        
        return [resource.to_dict() for resource in resources]
    
    def update_resource(self, name: str, spec: Dict) -> Dict:
        """Update an existing resource"""
        tenant_id = get_current_tenant()
        
        resource = Resource.query.filter_by(
            tenant_id=tenant_id,
            name=name,
            resource_type=self.resource_type
        ).first()
        
        if not resource:
            raise ValueError(f"Resource {name} not found")
        
        if not self.validate_spec(spec):
            raise ValueError(f"Invalid spec for {self.resource_type}")
        
        try:
            # Generate updated manifest
            manifest = self.generate_manifest(name, spec, tenant_id)
            manifest_path = self.gitops.deploy_manifest(
                tenant_id, self.resource_type, name, manifest
            )
            
            # Update resource
            resource.spec = spec
            resource.status = 'syncing'
            resource.manifest_path = manifest_path
            
            # Sync ArgoCD application
            if resource.argocd_app_name:
                self.argocd.sync_application(resource.argocd_app_name)
            
            # Log operation
            operation = ResourceOperation(
                resource_id=resource.id,
                tenant_id=tenant_id,
                operation='update',
                status='success',
                details={'manifest_path': manifest_path}
            )
            
            db.session.add(operation)
            db.session.commit()
            
            return resource.to_dict()
            
        except Exception as e:
            logger.error(f"Failed to update resource {name}: {str(e)}")
            
            operation = ResourceOperation(
                resource_id=resource.id,
                tenant_id=tenant_id,
                operation='update',
                status='failed',
                error_message=str(e)
            )
            
            db.session.add(operation)
            db.session.commit()
            raise
    
    def delete_resource(self, name: str) -> bool:
        """Delete a resource"""
        tenant_id = get_current_tenant()
        
        resource = Resource.query.filter_by(
            tenant_id=tenant_id,
            name=name,
            resource_type=self.resource_type
        ).first()
        
        if not resource:
            return False
        
        try:
            # Delete ArgoCD application
            if resource.argocd_app_name:
                self.argocd.delete_application(resource.argocd_app_name)
            
            # Delete manifest from Git
            if resource.manifest_path:
                self.gitops.delete_manifest(resource.manifest_path)
            
            # Log operation
            operation = ResourceOperation(
                resource_id=resource.id,
                tenant_id=tenant_id,
                operation='delete',
                status='success'
            )
            
            db.session.add(operation)
            db.session.delete(resource)
            db.session.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete resource {name}: {str(e)}")
            
            operation = ResourceOperation(
                resource_id=resource.id,
                tenant_id=tenant_id,
                operation='delete',
                status='failed',
                error_message=str(e)
            )
            
            db.session.add(operation)
            db.session.commit()
            raise
    
    def get_status(self, name: str) -> Dict:
        """Get resource status from ArgoCD"""
        tenant_id = get_current_tenant()
        
        resource = Resource.query.filter_by(
            tenant_id=tenant_id,
            name=name,
            resource_type=self.resource_type
        ).first()
        
        if not resource:
            raise ValueError(f"Resource {name} not found")
        
        status = {
            'name': name,
            'resource_type': self.resource_type,
            'status': resource.status,
            'created_at': resource.created_at.isoformat(),
            'updated_at': resource.updated_at.isoformat()
        }
        
        if resource.argocd_app_name:
            argocd_status = self.argocd.get_application_status(resource.argocd_app_name)
            if argocd_status:
                status.update(argocd_status)
        
        return status