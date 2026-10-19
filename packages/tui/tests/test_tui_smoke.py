import shutil
import subprocess

import pytest

from subeventually_tui import __version__
from subeventually_tui.cli import main


def test_main_without_arguments_succeeds() -> None:
    assert main([]) == 0


def test_main_prints_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["--version"])
    assert exc_info.value.code == 0
    assert capsys.readouterr().out == f"subeventually {__version__}\n"


def test_console_script_prints_version() -> None:
    executable = shutil.which("subeventually")
    assert executable is not None, "the subeventually console script is not on PATH"
    result = subprocess.run([executable, "--version"], capture_output=True, text=True, check=True)
    assert result.stdout.strip() == f"subeventually {__version__}"
