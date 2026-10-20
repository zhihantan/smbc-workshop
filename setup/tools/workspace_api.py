"""Call the Databricks REST API from a laptop or from a notebook. Shared by the setup notebooks, dashboards.py and
genie_agents.py.

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


def can_use(warehouse_id):
    """Whether you can run queries on the warehouse: runs SELECT 1, which starts the warehouse if it's stopped."""
    try:
        r = api("post", "/api/2.0/sql/statements", {"warehouse_id": warehouse_id, "statement": "SELECT 1",
                                                    "wait_timeout": "30s", "on_wait_timeout": "CONTINUE"})
    except ApiError:
        return False
    return r.get("status", {}).get("state") != "FAILED"


def pick_warehouse(preferred=""):
    """The SQL warehouse to use: `preferred` (a name or ID) if it's set, otherwise the first one you can use, serverless
    before pro and running before stopped. Classic warehouses are skipped, because Genie Agents need pro or serverless."""
    found = api("get", "/api/2.0/sql/warehouses").get("warehouses", [])
    if preferred:
        candidates = [wh for wh in found if preferred in (wh["id"], wh["name"])]
        if not candidates:
            raise ApiError(f"There's no SQL warehouse called '{preferred}' that you can see.")
    else:
        candidates = sorted((wh for wh in found if wh.get("enable_serverless_compute") or wh.get("warehouse_type") == "PRO"),
                            key=lambda wh: (not wh.get("enable_serverless_compute"), wh.get("state") != "RUNNING", wh["name"]))
    for wh in candidates:
        if can_use(wh["id"]):
            return wh
    raise ApiError(f"You can't run queries on {'that warehouse' if preferred else 'any pro or serverless SQL warehouse'}. "
                   "Ask a workspace admin for CAN USE on one (guide 3.4).")
