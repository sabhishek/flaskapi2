import os
import git
import yaml
import shutil
from pathlib import Path
from typing import Dict, Optional
from flask import current_app
import logging

logger = logging.getLogger(__name__)

class GitOpsManager:
    """Manages Git operations for manifest deployment"""
    
    def __init__(self):
        self.repo_url = current_app.config.get('GIT_REPO_URL')
        self.branch = current_app.config.get('GIT_BRANCH', 'main')
        self.username = current_app.config.get('GIT_USERNAME')
        self.password = current_app.config.get('GIT_PASSWORD')
        self.manifests_dir = current_app.config.get('MANIFESTS_DIR', 'manifests')
        self.local_repo_path = '/tmp/infrastructure-manifests'
    
    def _clone_or_pull_repo(self):
        """Clone repository or pull latest changes"""
        if os.path.exists(self.local_repo_path):
            try:
                repo = git.Repo(self.local_repo_path)
                origin = repo.remotes.origin
                origin.pull()
                logger.info("Repository updated successfully")
                return repo
            except Exception as e:
                logger.warning(f"Failed to pull repository: {e}")
                # Remove and re-clone
                shutil.rmtree(self.local_repo_path)
        
        try:
            # Clone repository
            repo = git.Repo.clone_from(
                self.repo_url,
                self.local_repo_path,
                branch=self.branch
            )
            logger.info("Repository cloned successfully")
            return repo
        except Exception as e:
            logger.error(f"Failed to clone repository: {e}")
            raise
    
    def _get_manifest_path(self, tenant_id: str, resource_type: str, name: str) -> str:
        """Generate manifest file path"""
        return os.path.join(
            self.local_repo_path,
            self.manifests_dir,
            tenant_id,
            resource_type,
            f"{name}.yaml"
        )
    
    def deploy_manifest(self, tenant_id: str, resource_type: str, name: str, manifest: str) -> str:
        """Deploy manifest to Git repository"""
        try:
            repo = self._clone_or_pull_repo()
            
            # Create directory structure
            manifest_path = self._get_manifest_path(tenant_id, resource_type, name)
            os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
            
            # Write manifest file
            with open(manifest_path, 'w') as f:
                f.write(manifest)
            
            # Add and commit changes
            repo.index.add([manifest_path])
            repo.index.commit(f"Deploy {resource_type} {name} for tenant {tenant_id}")
            
            # Push changes
            origin = repo.remotes.origin
            origin.push()
            
            logger.info(f"Manifest deployed successfully: {manifest_path}")
            return manifest_path
            
        except Exception as e:
            logger.error(f"Failed to deploy manifest: {e}")
            raise
    
    def delete_manifest(self, manifest_path: str):
        """Delete manifest from Git repository"""
        try:
            repo = self._clone_or_pull_repo()
            
            if os.path.exists(manifest_path):
                os.remove(manifest_path)
                repo.index.remove([manifest_path])
                repo.index.commit(f"Delete manifest: {os.path.basename(manifest_path)}")
                
                # Push changes
                origin = repo.remotes.origin
                origin.push()
                
                logger.info(f"Manifest deleted successfully: {manifest_path}")
            else:
                logger.warning(f"Manifest not found: {manifest_path}")
                
        except Exception as e:
            logger.error(f"Failed to delete manifest: {e}")
            raise
    
    def get_tenant_manifests(self, tenant_id: str) -> Dict:
        """Get all manifests for a tenant"""
        try:
            repo = self._clone_or_pull_repo()
            
            tenant_path = os.path.join(
                self.local_repo_path,
                self.manifests_dir,
                tenant_id
            )
            
            manifests = {}
            
            if os.path.exists(tenant_path):
                for root, dirs, files in os.walk(tenant_path):
                    for file in files:
                        if file.endswith('.yaml') or file.endswith('.yml'):
                            file_path = os.path.join(root, file)
                            relative_path = os.path.relpath(file_path, tenant_path)
                            
                            with open(file_path, 'r') as f:
                                manifests[relative_path] = yaml.safe_load(f.read())
            
            return manifests
            
        except Exception as e:
            logger.error(f"Failed to get tenant manifests: {e}")
            raise