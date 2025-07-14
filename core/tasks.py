from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import git
import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape
from flask import current_app as flask_app
from types import SimpleNamespace
from core.gitops import GitOpsManager

logger = logging.getLogger(__name__)


def _get_templates_repo() -> Path:
    """Clone or pull the infra-templates repo and return its local path."""

    repo_url = flask_app.config["TEMPLATE_REPO_URL"]
    branch = flask_app.config.get("TEMPLATE_REPO_BRANCH", "main")
    local_path = Path("/tmp/infra-templates")

    if local_path.exists():
        try:
            repo = git.Repo(local_path)
            repo.remotes.origin.pull()
            return local_path
        except Exception as exc:  # pragma: no cover
            logger.warning("Failed to pull templates repo – recloning: %s", exc)
            import shutil

            shutil.rmtree(local_path)

    git.Repo.clone_from(repo_url, local_path, branch=branch)
    return local_path


def _render_manifest(job: "Job") -> tuple[str, str]:
    """Create YAML manifest text and return (content, relative_path_in_repo)."""

    # ------------------------------------------------------------------
    # Determine cluster-aware path from resource_configs.yaml
    # ------------------------------------------------------------------

    config_path = Path(__file__).resolve().parent.parent / "resource_configs.yaml"
    if not config_path.exists():  # pragma: no cover
        raise FileNotFoundError("resource_configs.yaml not found for manifest rules")

    cfg = yaml.safe_load(config_path.read_text()) or {}
    resource_cfg: dict[str, Any] = cfg.get(job.resource_type, {})
    cluster_aware = bool(resource_cfg.get("cluster_aware", False))

    if cluster_aware:
        manifest_rel_path = (
            f"{job.resource_type}s/{job.cluster_id}/{job.tenant_id}/{job.resource_name}.yaml"
        )
    else:
        manifest_rel_path = f"{job.resource_type}s/{job.tenant_id}/{job.resource_name}.yaml"

    # ------------------------------------------------------------------
    # Render Jinja2 template from infra-templates repo
    # ------------------------------------------------------------------

    templates_path = _get_templates_repo()
    flavor = (job.spec or {}).get("flavor", "default")
    template_file = f"{job.resource_type}/{flavor}.yaml.j2"
    template_path = templates_path / template_file

    if not template_path.exists():
        raise FileNotFoundError(f"Template {template_file} not found in infra-templates repo")

    env = Environment(
        loader=FileSystemLoader(str(templates_path)),
        autoescape=select_autoescape(enabled_extensions=(".yaml", ".yml")),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    template = env.get_template(template_file)

    # Variables available to the template
    context = {
        "name": job.resource_name,
        "tenant_id": job.tenant_id,
        "cluster_id": job.cluster_id,
        **(job.spec or {}),
    }

    manifest_yaml = template.render(context)

    return manifest_yaml, manifest_rel_path


# ----------------------------------------------------------------------------
# Celery task entry-points
# ----------------------------------------------------------------------------

from celery_worker import celery  # import the shared Celery app


@celery.task(name="core.tasks.process_job", bind=True)
def process_job(self, job_id: str) -> str:  # noqa: D401
    """Celery task that processes an async Job identified by *job_id*.

    The heavy-lifting logic should live in :py:class:`core.job_manager.JobManager`.
    Here we simply hand off to it so that the worker stays skinny.
    """
    logger.info("Celery worker picked up job %s", job_id)

    # Import here to avoid circular dependencies at import-time.
    from core.job_manager import JobManager, JobStatus  # local import

    jm = JobManager(app=flask_app)

    try:
        jm.update_job_status(job_id, JobStatus.IN_PROGRESS)

        # Retrieve job payload (dict) and convert to object for _render_manifest
        job_data = jm.get_job_status(job_id)
        if not job_data:
            raise ValueError(f"Job {job_id} not found")
        job_obj = SimpleNamespace(**job_data)

        # Render manifest YAML
        manifest_yaml, rel_path = _render_manifest(job_obj)

        # Commit manifest to Git repository
        gom = GitOpsManager()
        commit_path = gom.deploy_manifest(
            tenant_id=job_obj.tenant_id,
            resource_type=job_obj.resource_type,
            name=job_obj.resource_name,
            manifest=manifest_yaml,
        )

        jm.update_job_status(
            job_id,
            JobStatus.COMPLETED,
            logs=[
                "Manifest rendered", 
                f"Manifest committed to {commit_path}"
            ],
            metadata={"manifest_path": rel_path},
        )
        logger.info("Job %s completed", job_id)
    except Exception as exc:  # pragma: no cover
        logger.exception("Job %s failed: %s", job_id, exc)
        jm.update_job_status(job_id, JobStatus.FAILED, logs=[str(exc)])
        raise self.retry(exc=exc, countdown=30, max_retries=3)

    return job_id
