import requests
import json
import logging
from typing import Dict, List, Optional
from core.resource_config import WebhookConfig
from flask import current_app

logger = logging.getLogger(__name__)

class WebhookManager:
    """Manages webhook notifications"""
    
    def __init__(self):
        self.timeout = current_app.config.get('WEBHOOK_TIMEOUT', 30)
        self.retries = current_app.config.get('WEBHOOK_RETRIES', 3)
        self.dev_mode = current_app.config.get('DEV_MODE', False)
    
    def send_webhook(self, webhook_config: WebhookConfig, job_id: str, 
                    status: str, tenant_id: str, resource_type: str,
                    resource_name: str, logs: List[str] = None,
                    metadata: Dict = None) -> bool:
        """Send webhook notification"""
        if not webhook_config or not webhook_config.enabled:
            return True
        
        payload = {
            'job_id': job_id,
            'status': status,
            'tenant_id': tenant_id,
            'resource_type': resource_type,
            'resource_name': resource_name,
            'timestamp': self._get_timestamp(),
            'logs': logs or [],
            'metadata': metadata or {}
        }
        
        if self.dev_mode:
            return self._simulate_webhook(webhook_config.url, payload)
        else:
            return self._send_real_webhook(webhook_config, payload)
    
    def _send_real_webhook(self, webhook_config: WebhookConfig, payload: Dict) -> bool:
        """Send actual webhook request"""
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'GitOps-API-Webhook/2.0'
        }
        
        for attempt in range(webhook_config.retries):
            try:
                response = requests.post(
                    webhook_config.url,
                    json=payload,
                    headers=headers,
                    timeout=webhook_config.timeout
                )
                
                if response.status_code in [200, 201, 202]:
                    logger.info(f"Webhook sent successfully to {webhook_config.url}")
                    return True
                else:
                    logger.warning(f"Webhook failed with status {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Webhook attempt {attempt + 1} failed: {e}")
                
            if attempt < webhook_config.retries - 1:
                # Wait before retry (exponential backoff)
                import time
                time.sleep(2 ** attempt)
        
        logger.error(f"All webhook attempts failed for {webhook_config.url}")
        return False
    
    def _simulate_webhook(self, url: str, payload: Dict) -> bool:
        """Simulate webhook in development mode"""
        logger.info(f"[DEV MODE] Simulating webhook to {url}")
        logger.info(f"[DEV MODE] Payload: {json.dumps(payload, indent=2)}")
        return True
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.utcnow().isoformat() + 'Z'
    
    def send_staged_webhook(self, webhook_config: WebhookConfig, job_id: str,
                           stage: str, tenant_id: str, resource_type: str,
                           resource_name: str, stage_data: Dict = None) -> bool:
        """Send staged webhook for multi-stage operations"""
        if webhook_config.mode != 'staged':
            return True
        
        payload = {
            'job_id': job_id,
            'stage': stage,
            'tenant_id': tenant_id,
            'resource_type': resource_type,
            'resource_name': resource_name,
            'timestamp': self._get_timestamp(),
            'stage_data': stage_data or {}
        }
        
        if self.dev_mode:
            return self._simulate_webhook(webhook_config.url, payload)
        else:
            return self._send_real_webhook(webhook_config, payload)