"""Call the Databricks REST API from a laptop or from a notebook. Shared by dashboards.py and genie_agents.py.

From a laptop, requests go through the Databricks CLI and a profile (`use_profile`). Inside Databricks, pass a
`databricks.sdk.WorkspaceClient()` to `use_client`; it authenticates as whoever runs the notebook, so no CLI or token
is needed.
"""
import json, re, subprocess

PROFILE = "DEFAULT"
CLIENT = None  # a databricks.sdk.WorkspaceClient when running inside Databricks


class ApiError(RuntimeError):
    pass


def use_profile(profile):
    global PROFILE, CLIENT
    PROFILE, CLIENT = profile, None


def use_client(client):
    global CLIENT
    CLIENT = client


def api(method, path, body=None):
    """Send one request and return the parsed JSON response. GET bodies are sent as query parameters."""
    method = method.lower()
    if CLIENT is not None:
        try:
            if method == "get":
                return CLIENT.api_client.do("GET", path, query=body) or {}
            return CLIENT.api_client.do(method.upper(), path, body=body) or {}
        except Exception as err:  # databricks.sdk.errors.DatabricksError and its subclasses
            raise ApiError(f"{method.upper()} {path} failed: {getattr(err, 'error_code', '')} {err}") from err
    cmd = ["databricks", "api", method, path, "-p", PROFILE] + (["--json", json.dumps(body)] if body is not None else [])
    out = subprocess.run(cmd, capture_output=True, text=True)
    if out.returncode:
        raise ApiError(f"{method.upper()} {path} failed: {out.stderr.strip()[:1500]}")
    return json.loads(out.stdout) if out.stdout.strip() else {}


def get_status(path):
    """The workspace object at `path` (object_id, resource_id, object_type), or None if there's nothing there."""
    try:
        return api("get", "/api/2.0/workspace/get-status", {"path": path})
    except ApiError as err:
        if "RESOURCE_DOES_NOT_EXIST" in str(err) or "doesn't exist" in str(err) or "does not exist" in str(err):
            return None
        raise


def principal(name):
    """ACL key for a principal: service principals are application IDs, users are emails, anything else is a group."""
    kind = ("service_principal_name" if re.fullmatch(r"[0-9a-f-]{36}", name)
            else "user_name" if "@" in name else "group_name")
    return {kind: name}


def share(object_type, object_id, name, level):
    """Add one permission, keeping the existing ones. object_type: dashboards, genie, notebooks, warehouses, ..."""
    api("patch", f"/api/2.0/permissions/{object_type}/{object_id}",
        {"access_control_list": [{**principal(name), "permission_level": level}]})
