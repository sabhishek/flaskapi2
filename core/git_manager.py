import os
import git
import shutil
from pathlib import Path
from typing import Dict, Optional
from flask import current_app
import logging

logger = logging.getLogger(__name__)

class GitManager:
    """Manages Git operations for multiple repositories"""
    
    def __init__(self):
        self.username = current_app.config.get('GIT_USERNAME')
        self.password = current_app.config.get('GIT_PASSWORD')
        self.template_repo_url = current_app.config.get('TEMPLATE_REPO_URL')
        self.template_branch = current_app.config.get('TEMPLATE_REPO_BRANCH', 'main')
        self.local_repos_path = '/tmp/gitops-repos'
        self.template_repo_path = '/tmp/infra-templates'
    
    def _get_repo_path(self, repo_url: str) -> str:
        """Get local path for a repository"""
        repo_name = repo_url.split('/')[-1].replace('.git', '')
        return os.path.join(self.local_repos_path, repo_name)
    
    def _clone_or_pull_repo(self, repo_url: str, branch: str = 'main') -> git.Repo:
        """Clone repository or pull latest changes"""
        repo_path = self._get_repo_path(repo_url)
        
        if os.path.exists(repo_path):
            try:
                repo = git.Repo(repo_path)
                origin = repo.remotes.origin
                origin.pull()
                logger.info(f"Repository updated: {repo_url}")
                return repo
            except Exception as e:
                logger.warning(f"Failed to pull repository: {e}")
                shutil.rmtree(repo_path)
        
        try:
            # Clone repository
            repo = git.Repo.clone_from(repo_url, repo_path, branch=branch)
            logger.info(f"Repository cloned: {repo_url}")
            return repo
        except Exception as e:
            logger.error(f"Failed to clone repository: {e}")
            raise
    
    def _get_manifest_path(self, repo_url: str, tenant_id: str, cluster_id: str,
                          resource_type: str, resource_name: str, cluster_aware: bool) -> str:
        """Generate manifest file path"""
        repo_path = self._get_repo_path(repo_url)
        
        if cluster_aware and cluster_id:
            path = os.path.join(
                repo_path, 'tenants', tenant_id, cluster_id, 
                resource_type, resource_name, 'manifest.yaml'
            )
        else:
            path = os.path.join(
                repo_path, 'tenants', tenant_id, 
                resource_type, resource_name, 'manifest.yaml'
            )
        
        return path
    
    def deploy_manifest(self, repo_url: str, tenant_id: str, cluster_id: str,
                       resource_type: str, resource_name: str, manifest: str,
                       cluster_aware: bool = True) -> str:
        """Deploy manifest to Git repository"""
        try:
            repo = self._clone_or_pull_repo(repo_url)
            
            # Create directory structure and write manifest
            manifest_path = self._get_manifest_path(
                repo_url, tenant_id, cluster_id, resource_type, 
                resource_name, cluster_aware
            )
            
            os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
            
            with open(manifest_path, 'w') as f:
                f.write(manifest)
            
            # Add and commit changes
            repo.index.add([manifest_path])
            commit_message = f"Deploy {resource_type} {resource_name} for tenant {tenant_id}"
            if cluster_aware and cluster_id:
                commit_message += f" in cluster {cluster_id}"
            
            repo.index.commit(commit_message)
            
            # Push changes
            origin = repo.remotes.origin
            origin.push()
            
            logger.info(f"Manifest deployed: {manifest_path}")
            return manifest_path
            
        except Exception as e:
            logger.error(f"Failed to deploy manifest: {e}")
            raise
    
    def delete_manifest(self, repo_url: str, tenant_id: str, cluster_id: str,
                       resource_type: str, resource_name: str, 
                       cluster_aware: bool = True) -> bool:
        """Delete manifest from Git repository"""
        try:
            repo = self._clone_or_pull_repo(repo_url)
            
            manifest_path = self._get_manifest_path(
                repo_url, tenant_id, cluster_id, resource_type,
                resource_name, cluster_aware
            )
            
            if os.path.exists(manifest_path):
                os.remove(manifest_path)
                
                # Remove empty directories
                manifest_dir = os.path.dirname(manifest_path)
                if os.path.exists(manifest_dir) and not os.listdir(manifest_dir):
                    os.rmdir(manifest_dir)
                
                repo.index.remove([manifest_path])
                commit_message = f"Delete {resource_type} {resource_name} for tenant {tenant_id}"
                if cluster_aware and cluster_id:
                    commit_message += f" in cluster {cluster_id}"
                
                repo.index.commit(commit_message)
                
                # Push changes
                origin = repo.remotes.origin
                origin.push()
                
                logger.info(f"Manifest deleted: {manifest_path}")
                return True
            else:
                logger.warning(f"Manifest not found: {manifest_path}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete manifest: {e}")
            raise
    
    def get_template(self, template_dir: str, flavor: str) -> Optional[str]:
        """Get template content from template repository"""
        try:
            # Clone or pull template repository
            if os.path.exists(self.template_repo_path):
                try:
                    repo = git.Repo(self.template_repo_path)
                    origin = repo.remotes.origin
                    origin.pull()
                except Exception:
                    shutil.rmtree(self.template_repo_path)
                    git.Repo.clone_from(
                        self.template_repo_url, 
                        self.template_repo_path, 
                        branch=self.template_branch
                    )
            else:
                git.Repo.clone_from(
                    self.template_repo_url, 
                    self.template_repo_path, 
                    branch=self.template_branch
                )
            
            # Find template file
            template_path = os.path.join(
                self.template_repo_path, template_dir, f"{flavor}.yaml.j2"
            )
            
            if os.path.exists(template_path):
                with open(template_path, 'r') as f:
                    return f.read()
            else:
                logger.warning(f"Template not found: {template_path}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get template: {e}")
            return None