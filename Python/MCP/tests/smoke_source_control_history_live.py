"""Verify paged revision metadata in the isolated two-commit Git fixture."""

import subprocess
from pathlib import Path

import httpx

PROJECT = Path(__file__).resolve().parents[5]
ROOT = PROJECT / "Saved" / "UE5MCP_SourceControl_Test"
ASSET = "/Game/SC_Test/T_SC_Smoke.T_SC_Smoke"
BASE = "http://127.0.0.1:8080"


def call(body):
    response = httpx.post(BASE + "/editor/source-control/history", json=body, timeout=180)
    response.raise_for_status()
    return response.json()


def verify_history(committed, latest):
    history = call({"AssetPaths": [ASSET], "MaxHistory": 1})
    assert history["success"] and history["history_supported"], history
    file_history = history["files"][0]
    assert Path(file_history["filename"]).resolve().is_relative_to((ROOT / "Content").resolve())
    assert file_history["history_total"] == 2 and file_history["returned_count"] == 1 and file_history["has_more"]
    revision = file_history["revisions"][0]
    assert latest.startswith(revision["revision"])
    assert "UE5MCP history second revision" in revision["description"]
    assert "UE5MCP Tests" in revision["user"] and revision["date"] and revision["size_bytes"] > 0
    older = call({"AssetPaths": [ASSET], "MaxHistory": 1, "HistoryOffset": 1, "bRefresh": False})["files"][0]
    assert older["returned_count"] == 1 and not older["has_more"]
    assert committed.startswith(older["revisions"][0]["revision"])
    empty = call({"AssetPaths": [ASSET], "HistoryOffset": 2, "bRefresh": False})["files"][0]
    assert not empty["revisions"] and empty["returned_count"] == 0 and not empty["has_more"]
    for limits in [{"MaxHistory": 0}, {"MaxHistory": 51}, {"HistoryOffset": -1}]:
        rejected = httpx.post(BASE + "/editor/source-control/history", json={"AssetPaths": [ASSET], **limits}, timeout=180)
        assert rejected.status_code >= 400


def main():
    def git(*args):
        return subprocess.check_output(["git", "-c", "safe.directory=" + ROOT.as_posix(),
                                        "-C", str(ROOT), *args], text=True).strip()
    assert Path(git("rev-parse", "--show-toplevel")).resolve() == ROOT.resolve()
    assert not git("remote")
    commits = git("log", "--format=%H", "--", "Content/SC_Test/T_SC_Smoke.uasset").splitlines()
    assert len(commits) == 2
    verify_history(commits[1], commits[0])
    print("Isolated Git revision metadata, paging, cache, and limit guards: OK")


if __name__ == "__main__":
    main()
