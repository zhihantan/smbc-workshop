#!/usr/bin/env python3
"""Create, find and run the job that rebuilds the SMBC workshop data every day (Jobs API).

The job **SMBC Workshop: daily data refresh** runs on serverless compute every day at 06:00 Singapore time, an hour
before the 07:00 schedule attendees give their Lab 1 pipeline. Each task starts when the one before it succeeds:

1. `generate_data`: `data/generate_data.py` writes the synthetic extracts to the landing volume. It's seeded, so every
   run writes the same files and the answer key still holds.
2. `build_bronze_silver_gold`: `setup/02_build_bronze_silver_gold` rebuilds the reference tables.
3. `validate_bronze_silver_gold`: `setup/03_validate_bronze_silver_gold` checks them against the answer key; the run
   fails if any check does, and whoever deployed the job gets an email.

The tasks run the files in the Git folder, so the job picks up whatever is pulled into it.

From a laptop, through the Databricks CLI:

  data_job.py --profile P deploy --repo "/Workspace/Users/<you>/smbc-workshop" --notify you@example.com
  data_job.py --profile P run                      # run it now and wait for the result
  data_job.py settings --repo ...                  # print the job settings only

Inside the workspace, `setup/06_deploy_dashboards_and_agents` creates the job without a laptop.
"""
import argparse, json, sys, time

import workspace_api
from workspace_api import api

NAME = "SMBC Workshop: daily data refresh"
CATALOG = "smbc_workshop"
SCHEDULE = {"quartz_cron_expression": "0 0 6 * * ?", "timezone_id": "Asia/Singapore", "pause_status": "UNPAUSED"}
WHEN = "every day at 06:00 Singapore time"


def settings(repo, notify=()):
    """The job settings. `repo` is the Git folder's workspace path; `notify` is who gets an email when a run fails."""
    repo = repo.rstrip("/").removeprefix("/Workspace")
    return {
        "name": NAME,
        "description": f"Regenerates the synthetic workshop data in /Volumes/{CATALOG}/raw, then rebuilds and validates "
                       "the bronze, silver and gold reference tables. Created by setup/06_deploy_dashboards_and_agents.",
        "schedule": SCHEDULE,
        "max_concurrent_runs": 1,
        "timeout_seconds": 3600,
        "email_notifications": {"on_failure": list(notify)},
        "environments": [{"environment_key": "default", "spec": {"environment_version": "2"}}],  # for the Python script
        "tasks": [
            {"task_key": "generate_data", "environment_key": "default",
             "spark_python_task": {"python_file": f"{repo}/data/generate_data.py",
                                   "parameters": ["--out", f"/Volumes/{CATALOG}/raw"]}},
            {"task_key": "build_bronze_silver_gold", "depends_on": [{"task_key": "generate_data"}],
             "notebook_task": {"notebook_path": f"{repo}/setup/02_build_bronze_silver_gold"}},
            {"task_key": "validate_bronze_silver_gold", "depends_on": [{"task_key": "build_bronze_silver_gold"}],
             "notebook_task": {"notebook_path": f"{repo}/setup/03_validate_bronze_silver_gold",
                               "base_parameters": {"catalog": CATALOG}}},
        ],
    }


def task_paths(job_settings):
    """The workspace paths the job's tasks run."""
    return [t.get("notebook_task", {}).get("notebook_path") or t.get("spark_python_task", {}).get("python_file")
            for t in job_settings.get("tasks", [])]


def find():
    """ID of the job called NAME in this workspace, or None."""
    jobs = api("get", "/api/2.1/jobs/list", {"name": NAME}).get("jobs", [])
    return jobs[0]["job_id"] if jobs else None


def create_or_update(repo, notify=()):
    """Create the job, or replace its settings if it already exists. Returns (job_id, created)."""
    job_id = find()
    if job_id is None:
        return api("post", "/api/2.1/jobs/create", settings(repo, notify))["job_id"], True
    api("post", "/api/2.1/jobs/reset", {"job_id": job_id, "new_settings": settings(repo, notify)})
    return job_id, False


def run(job_id, wait=True):
    """Start a run now. Returns the run (state, run_page_url, tasks); with `wait`, once it has finished."""
    run_id = api("post", "/api/2.1/jobs/run-now", {"job_id": job_id})["run_id"]
    while True:
        result = api("get", "/api/2.1/jobs/runs/get", {"run_id": run_id})
        if not wait or result["state"]["life_cycle_state"] in ("TERMINATED", "SKIPPED", "INTERNAL_ERROR"):
            return result
        time.sleep(15)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["deploy", "run", "settings"])
    ap.add_argument("--profile", "-p", default="DEFAULT")
    ap.add_argument("--repo", help="workspace path of the Git folder (deploy, settings)")
    ap.add_argument("--notify", default="", help="emails to tell when a run fails, comma-separated (deploy)")
    a = ap.parse_args()
    workspace_api.use_profile(a.profile)
    if a.cmd in ("deploy", "settings") and not a.repo:
        sys.exit("--repo is required: the workspace path of the Git folder, e.g. /Workspace/Users/<you>/smbc-workshop")
    if a.cmd == "settings":
        print(json.dumps(settings(a.repo), indent=2))
    elif a.cmd == "deploy":
        job_id, created = create_or_update(a.repo, [e.strip() for e in a.notify.split(",") if e.strip()])
        print(f"{NAME}: job {job_id} ({'created' if created else 'updated'}), runs {WHEN}")
    else:
        job_id = find()
        if job_id is None:
            sys.exit(f"There's no job called '{NAME}': deploy it first.")
        result = run(job_id)
        print(result["state"].get("result_state") or result["state"]["life_cycle_state"], result["run_page_url"])
        for task in result.get("tasks", []):
            print(f"  {task['task_key']}: {task['state'].get('result_state')}")


if __name__ == "__main__":
    try:
        main()
    except workspace_api.ApiError as err:
        sys.exit(str(err))
