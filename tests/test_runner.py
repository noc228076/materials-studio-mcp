from pathlib import Path

from material_studio_mcp_server.config import MaterialStudioConfig
from material_studio_mcp_server.runner import MaterialStudioRunner, _materials_run_succeeded


def test_build_default_command_for_runmatscript_uses_script_stem(tmp_path: Path) -> None:
    runner_path = tmp_path / "Program Files" / "BIOVIA" / "RunMatScript.bat"
    script_path = tmp_path / "jobs" / "script.pl"
    config = MaterialStudioConfig(
        runner=runner_path,
        workspace_root=tmp_path,
        default_timeout_seconds=10,
        install_home=None,
        runner_source="test",
        extra_runner_args=("--foo", "bar baz"),
    )

    command = MaterialStudioRunner(config)._build_command(runner_path, script_path, ["--x", "1 2"])

    assert command == [str(runner_path), "--foo", "bar baz", "script", "--", "--x", "1 2"]


def test_build_default_command_for_other_runner_uses_script_path(tmp_path: Path) -> None:
    runner_path = tmp_path / "RunMatserver.bat"
    script_path = tmp_path / "jobs" / "script.pl"
    config = MaterialStudioConfig(
        runner=runner_path,
        workspace_root=tmp_path,
        default_timeout_seconds=10,
        install_home=None,
        runner_source="test",
        extra_runner_args=(),
    )

    command = MaterialStudioRunner(config)._build_command(runner_path, script_path, [])

    assert command == [str(runner_path), str(script_path)]


def test_materials_log_failure_detection() -> None:
    assert not _materials_run_succeeded(0, "", "Completion status: (FAIL).")
    assert _materials_run_succeeded(0, "ok", "Completion status: (OK).")
