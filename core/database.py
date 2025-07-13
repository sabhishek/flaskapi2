from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

db = SQLAlchemy()

class BaseModel(db.Model):
    """Base model with common fields"""
    __abstract__ = True
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(100), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.String(100))
    
    def to_dict(self):
        """Convert model to dictionary"""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            result[column.name] = value
        return result

class Resource(BaseModel):
    """Base resource model"""
    __tablename__ = 'resources'
    
    name = db.Column(db.String(100), nullable=False)
    resource_type = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), default='pending')
    spec = db.Column(db.JSON)
    manifest_path = db.Column(db.String(255))
    argocd_app_name = db.Column(db.String(100))
    
    # Composite index for tenant + resource type queries
    __table_args__ = (
        db.Index('idx_tenant_resource_type', 'tenant_id', 'resource_type'),
        db.Index('idx_tenant_name', 'tenant_id', 'name'),
    )
    
    def __repr__(self):
        return f'<Resource {self.name} ({self.resource_type})>'

class ResourceOperation(BaseModel):
    """Track resource operations for audit"""
    __tablename__ = 'resource_operations'
    
    resource_id = db.Column(db.String(36), db.ForeignKey('resources.id'), nullable=False)
    operation = db.Column(db.String(50), nullable=False)  # create, update, delete
    status = db.Column(db.String(50), default='pending')  # pending, success, failed
    details = db.Column(db.JSON)
    error_message = db.Column(db.Text)
    
    resource = db.relationship('Resource', backref='operations')
    
    def __repr__(self):
        return f'<ResourceOperation {self.operation} for {self.resource_id}>'

class Job(BaseModel):
    """Persist asynchronous jobs submitted through the API."""
    __tablename__ = "jobs"

    job_id = db.Column(db.String(36), unique=True, nullable=False)
    job_type = db.Column(db.String(50))
    cluster_id = db.Column(db.String(100))
    resource_type = db.Column(db.String(50))
    resource_name = db.Column(db.String(100))
    operation = db.Column(db.String(50))
    spec = db.Column(db.JSON)
    status = db.Column(db.String(50), default="submitted")
    logs = db.Column(db.JSON, default=list)
    metadata = db.Column(db.JSON, default=dict)

    def __repr__(self):
        return f"<Job {self.job_id} ({self.status})>"