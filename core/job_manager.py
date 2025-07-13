import uuid
import json
from datetime import datetime
from typing import Dict, Optional, List
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class JobStatus(Enum):
    SUBMITTED = "submitted"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class JobManager:
    """Manages async job processing"""
    
    def __init__(self, app=None):
        self.app = app
        self.dev_mode = app.config.get('DEV_MODE', False) if app else True
        
        if self.dev_mode:
            # In-memory storage for development
            self.jobs = {}
        else:
            # Initialize Celery for production
            self._init_celery()
    
    def _init_celery(self):
        """Initialize Celery for production mode"""
        try:
            from celery import Celery
            self.celery = Celery(
                self.app.import_name,
                broker=self.app.config['CELERY_BROKER_URL'],
                backend=self.app.config['CELERY_RESULT_BACKEND']
            )
            self.celery.conf.update(self.app.config)
        except ImportError:
            logger.warning("Celery not available, falling back to dev mode")
            self.dev_mode = True
            self.jobs = {}
    
    def submit_job(self, job_type: str, tenant_id: str, cluster_id: str, 
                   resource_type: str, resource_name: str, operation: str, 
                   spec: Dict = None) -> str:
        """Submit a new job and return job_id"""
        job_id = str(uuid.uuid4())
        
        job_data = {
            'job_id': job_id,
            'job_type': job_type,
            'tenant_id': tenant_id,
            'cluster_id': cluster_id,
            'resource_type': resource_type,
            'resource_name': resource_name,
            'operation': operation,
            'spec': spec or {},
            'status': JobStatus.SUBMITTED.value,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
            'logs': [],
            'metadata': {}
        }
        
        if self.dev_mode:
            self.jobs[job_id] = job_data
            # Simulate async processing in dev mode
            self._simulate_job_processing(job_id)
        else:
            # Store in database and queue with Celery
            self._store_job(job_data)
            self._queue_job(job_id)
        
        return job_id
    
    def get_job_status(self, job_id: str) -> Optional[Dict]:
        """Get job status and details"""
        if self.dev_mode:
            return self.jobs.get(job_id)
        else:
            return self._get_job_from_db(job_id)
    
    def update_job_status(self, job_id: str, status: JobStatus, 
                         logs: List[str] = None, metadata: Dict = None):
        """Update job status"""
        if self.dev_mode:
            if job_id in self.jobs:
                self.jobs[job_id]['status'] = status.value
                self.jobs[job_id]['updated_at'] = datetime.utcnow().isoformat()
                if logs:
                    self.jobs[job_id]['logs'].extend(logs)
                if metadata:
                    self.jobs[job_id]['metadata'].update(metadata)
        else:
            self._update_job_in_db(job_id, status, logs, metadata)
    
    def _simulate_job_processing(self, job_id: str):
        """Simulate job processing in development mode"""
        import threading
        import time
        
        def process_job():
            time.sleep(2)  # Simulate processing time
            self.update_job_status(
                job_id, 
                JobStatus.IN_PROGRESS,
                logs=["Job started", "Processing manifest"]
            )
            
            time.sleep(3)  # More processing
            self.update_job_status(
                job_id,
                JobStatus.COMPLETED,
                logs=["Manifest generated", "Git commit successful", "Webhook sent"],
                metadata={"git_commit": "abc123", "webhook_status": "sent"}
            )
        
        thread = threading.Thread(target=process_job)
        thread.daemon = True
        thread.start()
    
    def _store_job(self, job_data: Dict):
        """Store job in database (production mode)"""
        from core.database import db, Job  # local import to avoid circular deps
        
        job_row = Job(
            job_id=job_data["job_id"],
            tenant_id=job_data["tenant_id"],
            job_type=job_data["job_type"],
            cluster_id=job_data["cluster_id"],
            resource_type=job_data["resource_type"],
            resource_name=job_data["resource_name"],
            operation=job_data["operation"],
            spec=job_data["spec"],
            status=job_data["status"],
            logs=job_data["logs"],
            metadata=job_data["metadata"],
        )
        
        db.session.add(job_row)
        db.session.commit()
 
    def _queue_job(self, job_id: str):
        """Queue job with Celery (production mode)"""
        try:
            # Send task name registered in core.tasks
            self.celery.send_task("core.tasks.process_job", args=[job_id])
        except Exception as exc:
            logger.exception("Failed to enqueue Celery job %s", job_id)
    
    def _get_job_from_db(self, job_id: str) -> Optional[Dict]:
        """Get job from database (production mode)"""
        from core.database import Job
        from core.database import db
        
        job_row = Job.query.filter_by(job_id=job_id).first()
        return job_row.to_dict() if job_row else None
    
    def _update_job_in_db(self, job_id: str, status: JobStatus, 
                         logs: List[str] = None, metadata: Dict = None):
        """Update job in database (production mode)"""
        from core.database import db, Job
        
        job_row = Job.query.filter_by(job_id=job_id).first()
        if not job_row:
            logger.warning("Job %s not found in DB while updating", job_id)
            return
        
        job_row.status = status.value
        if logs:
            job_row.logs = (job_row.logs or []) + logs
        if metadata:
            md = job_row.metadata or {}
            md.update(metadata)
            job_row.metadata = md
        db.session.commit()