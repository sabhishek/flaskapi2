from .namespace import NamespaceManager
from .vm import VMManager
from .app import AppManager
from .database import DatabaseManager

# Registry for resource managers
RESOURCE_MANAGERS = {
    'namespace': NamespaceManager,
    'vm': VMManager,
    'app': AppManager,
    'database': DatabaseManager
}

def get_resource_manager(resource_type: str):
    """Get resource manager instance"""
    manager_class = RESOURCE_MANAGERS.get(resource_type)
    if not manager_class:
        raise ValueError(f"Unknown resource type: {resource_type}")
    return manager_class()

def register_resource_manager(resource_type: str, manager_class):
    """Register a new resource manager"""
    RESOURCE_MANAGERS[resource_type] = manager_class

def list_resource_types():
    """List all available resource types"""
    return list(RESOURCE_MANAGERS.keys())