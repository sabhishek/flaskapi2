{{ ... }}
+import git
+from jinja2 import Environment, FileSystemLoader, select_autoescape
+
+
+# ---------------------------------------------------------------------------
+# Template handling
+# ---------------------------------------------------------------------------
+
+
+def _get_templates_repo() -> Path:
+    """Clone or pull the infra-templates repo and return its local path."""
+
+    repo_url = flask_app.config.get("TEMPLATE_REPO_URL")
+    branch = flask_app.config.get("TEMPLATE_REPO_BRANCH", "main")
+    local_path = Path("/tmp/infra-templates")
+
+    if local_path.exists():
+        try:
+            repo = git.Repo(local_path)
+            repo.remotes.origin.pull()
+            return local_path
+        except Exception as exc:  # pragma: no cover
+            logger.warning("Failed to pull templates repo – recloning: %s", exc)
+            import shutil
+
+            shutil.rmtree(local_path)
+
+    git.Repo.clone_from(repo_url, local_path, branch=branch)
+    return local_path
+
+
 def _render_manifest(job: Job) -> tuple[str, str]:
     """Create YAML manifest text and return (content, relative_path_in_repo)."""
-
-    # Decide cluster-aware directory structure by reading resoure_configs.yaml
-    config_path = Path(__file__).resolve().parent.parent / "resoure_configs.yaml"
-    if not config_path.exists():
-        raise FileNotFoundError("resoure_configs.yaml not found for manifest rules")
-
-    cfg = yaml.safe_load(config_path.read_text()) or {}
-    resource_cfg: dict[str, Any] = cfg.get(job.resource_type, {})
-    cluster_aware = bool(resource_cfg.get("cluster_aware", False))
-
-    # Build the repository path
-    if cluster_aware:
-        manifest_rel_path = f"namespaces/{job.cluster_id}/{job.tenant_id}/{job.resource_name}.yaml"
-    else:
-        manifest_rel_path = f"namespaces/{job.tenant_id}/{job.resource_name}.yaml"
-
-    # Simple Kubernetes Namespace manifest
-    manifest_dict = {
-        "apiVersion": "v1",
-        "kind": "Namespace",
-        "metadata": {
-            "name": job.resource_name,
-            "labels": job.spec.get("labels", {}),
-        },
-    }
-
-    manifest_yaml = yaml.safe_dump(manifest_dict, sort_keys=False)
-    return manifest_yaml, manifest_rel_path
+
+    # ------------------------------------------------------------------
+    # Determine cluster-aware path from resource_configs.yaml
+    # ------------------------------------------------------------------
+
+    config_path = Path(__file__).resolve().parent.parent / "resoure_configs.yaml"
+    if not config_path.exists():  # pragma: no cover
+        raise FileNotFoundError("resoure_configs.yaml not found for manifest rules")
+
+    cfg = yaml.safe_load(config_path.read_text()) or {}
+    resource_cfg: dict[str, Any] = cfg.get(job.resource_type, {})
+    cluster_aware = bool(resource_cfg.get("cluster_aware", False))
+
+    if cluster_aware:
+        manifest_rel_path = f"{job.resource_type}s/{job.cluster_id}/{job.tenant_id}/{job.resource_name}.yaml"
+    else:
+        manifest_rel_path = f"{job.resource_type}s/{job.tenant_id}/{job.resource_name}.yaml"
+
+    # ------------------------------------------------------------------
+    # Render Jinja2 template from infra-templates repo
+    # ------------------------------------------------------------------
+
+    templates_path = _get_templates_repo()
+    flavor = (job.spec or {}).get("flavor", "default")
+    template_file = f"{job.resource_type}/{flavor}.yaml.j2"
+    template_path = templates_path / template_file
+
+    if not template_path.exists():
+        raise FileNotFoundError(f"Template {template_file} not found in infra-templates repo")
+
+    env = Environment(
+        loader=FileSystemLoader(str(templates_path)),
+        autoescape=select_autoescape(enabled_extensions=(".yaml", ".yml")),
+        trim_blocks=True,
+        lstrip_blocks=True,
+    )
+
+    template = env.get_template(template_file)
+
+    # Variables available to the template
+    context = {
+        "name": job.resource_name,
+        "tenant_id": job.tenant_id,
+        "cluster_id": job.cluster_id,
+        **(job.spec or {}),
+    }
+
+    manifest_yaml = template.render(context)
+
+    return manifest_yaml, manifest_rel_path
