from pathlib import Path

from material_studio_mcp_server.config import resolve_config


def test_resolve_runner_from_env(monkeypatch, tmp_path: Path) -> None:
    runner = tmp_path / "RunMatserver.bat"
    runner.write_text("@echo off\n", encoding="utf-8")
    monkeypatch.setenv("MATERIAL_STUDIO_RUNNER", str(runner))
    monkeypatch.setenv("MATERIAL_STUDIO_WORKSPACE", str(tmp_path / "jobs"))

    config = resolve_config(cwd=tmp_path)

    assert config.runner == runner.resolve()
    assert config.runner_source == "MATERIAL_STUDIO_RUNNER"
    assert config.workspace_root == (tmp_path / "jobs").resolve()
