#!/usr/bin/env python3
"""Create or update the walkthrough Google Doc from facilitator/dist/Workshop_Walkthrough.docx.

  .venv/bin/python facilitator/publish_walkthrough.py                  # create a new Google Doc in your Drive
  .venv/bin/python facilitator/publish_walkthrough.py --doc-id ID      # replace the content of an existing one

The current walkthrough is https://docs.google.com/document/d/1MLrO4tmZqqT-gfEZGgpPYdAxb23aSw9SOWwzn88GN90
(--doc-id 1MLrO4tmZqqT-gfEZGgpPYdAxb23aSw9SOWwzn88GN90).

Uploads the .docx with conversion to a Google Doc; its linked contents list survives the conversion. Nothing is
shared: the doc stays private to you. Authenticates with gcloud
application-default credentials that have the Drive scope (gcloud needs Python 3.10+: set CLOUDSDK_PYTHON), billed
to the Databricks Field Engineering quota project.
"""
import argparse
import json
import os
import subprocess
import urllib.request
import uuid

from build_walkthrough import OUT_DOCX

QUOTA_PROJECT = "gcp-dev-field-eng-aiapiquota"
NAME = "SMBC Data & AI Workshop: full walkthrough (22 Oct 2026)"
DESCRIPTION = "Facilitator guide, attendee guide, workspace setup and presenter script. Built by facilitator/build_walkthrough.py. All data is synthetic."
DOCX_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def access_token():
    out = subprocess.run(["gcloud", "auth", "application-default", "print-access-token"], capture_output=True, text=True)
    if out.returncode:
        raise SystemExit(f"gcloud couldn't provide a token: {out.stderr.strip()[:300]}")
    return out.stdout.strip()


def call(method, url, token, body=None, raw=None, content_type="application/json"):
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    headers = {"Authorization": f"Bearer {token}", "x-goog-user-project": QUOTA_PROJECT}
    if data is not None:
        headers["Content-Type"] = content_type
    with urllib.request.urlopen(urllib.request.Request(url, data=data, method=method, headers=headers)) as resp:
        return json.loads(resp.read() or b"{}")


def upload(token, doc_id=None):
    """Create a Google Doc from the .docx, or replace an existing doc's content with it."""
    metadata = {"name": NAME, "description": DESCRIPTION}
    if not doc_id:
        metadata["mimeType"] = "application/vnd.google-apps.document"
    boundary = uuid.uuid4().hex
    with open(OUT_DOCX, "rb") as fh:
        body = (f"--{boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n{json.dumps(metadata)}\r\n"
                f"--{boundary}\r\nContent-Type: {DOCX_TYPE}\r\n\r\n").encode() + fh.read() + f"\r\n--{boundary}--".encode()
    url = ("https://www.googleapis.com/upload/drive/v3/files" + (f"/{doc_id}" if doc_id else "")
           + "?uploadType=multipart&fields=id,webViewLink")
    return call("PATCH" if doc_id else "POST", url, token, raw=body, content_type=f"multipart/related; boundary={boundary}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--doc-id", help="update this Google Doc instead of creating a new one")
    args = ap.parse_args()
    if not os.path.exists(OUT_DOCX):
        raise SystemExit("Run facilitator/build_walkthrough.py first.")
    token = access_token()
    doc = upload(token, args.doc_id)
    print(f"{'Updated' if args.doc_id else 'Created'} {doc.get('webViewLink', doc['id'])}")


if __name__ == "__main__":
    main()
