import requests
import json
import logging
from typing import Dict, Optional, List
from flask import current_app

logger = logging.getLogger(__name__)

class ArgoCDClient:
    """Client for ArgoCD API operations"""
    
    def __init__(self):
        self.base_url = current_app.config.get('ARGOCD_URL')
        self.username = current_app.config.get('ARGOCD_USERNAME')
        self.password = current_app.config.get('ARGOCD_PASSWORD')
        self.token = current_app.config.get('ARGOCD_TOKEN')
        self.session = requests.Session()
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with ArgoCD"""
        if self.token:
            self.session.headers.update({
                'Authorization': f'Bearer {self.token}'
            })
        elif self.username and self.password:
            try:
                auth_url = f"{self.base_url}/api/v1/session"
                response = self.session.post(auth_url, json={
                    'username': self.username,
                    'password': self.password
                })
                
                if response.status_code == 200:
                    token = response.json().get('token')
                    self.session.headers.update({
                        'Authorization': f'Bearer {token}'
                    })
                    logger.info("ArgoCD authentication successful")
                else:
                    logger.error(f"ArgoCD authentication failed: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"Failed to authenticate with ArgoCD: {e}")
    
    def create_application(self, app_name: str, tenant_id: str, resource_type: str) -> bool:
        """Create ArgoCD application"""
        try:
            app_spec = {
                'apiVersion': 'argoproj.io/v1alpha1',
                'kind': 'Application',
                'metadata': {
                    'name': app_name,
                    'namespace': 'argocd'
                },
                'spec': {
                    'project': 'default',
                    'source': {
                        'repoURL': current_app.config.get('GIT_REPO_URL'),
                        'targetRevision': current_app.config.get('GIT_BRANCH', 'main'),
                        'path': f"manifests/{tenant_id}/{resource_type}"
                    },
                    'destination': {
                        'server': 'https://kubernetes.default.svc',
                        'namespace': f"{tenant_id}-{resource_type}"
                    },
                    'syncPolicy': {
                        'automated': {
                            'prune': True,
                            'selfHeal': True
                        }
                    }
                }
            }
            
            url = f"{self.base_url}/api/v1/applications"
            response = self.session.post(url, json=app_spec)
            
            if response.status_code in [200, 201]:
                logger.info(f"ArgoCD application created: {app_name}")
                return True
            else:
                logger.error(f"Failed to create ArgoCD application: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to create ArgoCD application: {e}")
            return False
    
    def get_application_status(self, app_name: str) -> Optional[Dict]:
        """Get application status from ArgoCD"""
        try:
            url = f"{self.base_url}/api/v1/applications/{app_name}"
            response = self.session.get(url)
            
            if response.status_code == 200:
                app_data = response.json()
                status = app_data.get('status', {})
                
                return {
                    'sync_status': status.get('sync', {}).get('status'),
                    'health_status': status.get('health', {}).get('status'),
                    'operation_state': status.get('operationState', {}).get('phase'),
                    'last_sync': status.get('reconciledAt'),
                    'resources': len(status.get('resources', []))
                }
            else:
                logger.warning(f"Application not found in ArgoCD: {app_name}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get application status: {e}")
            return None
    
    def sync_application(self, app_name: str) -> bool:
        """Trigger application sync"""
        try:
            url = f"{self.base_url}/api/v1/applications/{app_name}/sync"
            response = self.session.post(url, json={})
            
            if response.status_code == 200:
                logger.info(f"ArgoCD sync triggered for: {app_name}")
                return True
            else:
                logger.error(f"Failed to sync ArgoCD application: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to sync ArgoCD application: {e}")
            return False
    
    def delete_application(self, app_name: str) -> bool:
        """Delete ArgoCD application"""
        try:
            url = f"{self.base_url}/api/v1/applications/{app_name}"
            response = self.session.delete(url)
            
            if response.status_code == 200:
                logger.info(f"ArgoCD application deleted: {app_name}")
                return True
            else:
                logger.error(f"Failed to delete ArgoCD application: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete ArgoCD application: {e}")
            return False
    
    def list_applications(self) -> List[Dict]:
        """List all applications"""
        try:
            url = f"{self.base_url}/api/v1/applications"
            response = self.session.get(url)
            
            if response.status_code == 200:
                return response.json().get('items', [])
            else:
                logger.error(f"Failed to list applications: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Failed to list applications: {e}")
            return []