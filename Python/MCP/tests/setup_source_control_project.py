"""Create an isolated content-only UE project and local Git repository for live tests."""

import json
import shutil
import subprocess
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[5]
ROOT = PROJECT / "Saved" / "UE5MCP_SourceControl_Test"


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True).strip()


def main():
    assert not ROOT.exists(), f"Test project already exists: {ROOT}"
    (ROOT / "Config").mkdir(parents=True)
    (ROOT / "Content").mkdir()
    project = {
        "FileVersion": 3, "EngineAssociation": "5.7",
        "AdditionalPluginDirectories": [str(PROJECT / "Plugins")],
        "Plugins": [{"Name": name, "Enabled": True}
                    for name in ["UE5_MCP", "GitSourceControl", "ControlRig", "RigVM"]],
    }
    (ROOT / "SourceControlFixture.uproject").write_text(json.dumps(project, indent=2), encoding="utf-8")
    (ROOT / ".gitignore").write_text("Saved/\nIntermediate/\nDerivedDataCache/\nBinaries/\n", encoding="utf-8")
    (ROOT / "Config" / "DefaultEditorPerProjectUserSettings.ini").write_text(
        "[/Script/UnrealEd.EditorLoadingSavingSettings]\n"
        "bSCCAutoAddNewFiles=False\n"
        "bAutomaticallyCheckoutOnAssetModification=False\n"
        "bPromptForCheckoutOnAssetModification=False\n", encoding="utf-8")
    binary = shutil.which("git")
    assert binary, "Git must be installed for the fixture"
    (ROOT / "Config" / "DefaultSourceControlSettings.ini").write_text(
        "[SourceControl.SourceControlSettings]\nProvider=Git\n"
        "[GitSourceControl.GitSourceControlSettings]\nBinaryPath=" +
        Path(binary).as_posix() + "\n", encoding="utf-8")
    git("init", "-b", "main")
    git("config", "--local", "user.name", "UE5MCP Tests")
    git("config", "--local", "user.email", "ue5mcp-tests@example.invalid")
    git("config", "--local", "commit.gpgsign", "false")
    git("config", "--local", "core.hooksPath", ".git/test-hooks")
    git("add", ".gitignore", "SourceControlFixture.uproject", "Config")
    git("commit", "-m", "Initial isolated source-control fixture")
    assert not git("remote")
    print(ROOT / "SourceControlFixture.uproject")


if __name__ == "__main__":
    main()
