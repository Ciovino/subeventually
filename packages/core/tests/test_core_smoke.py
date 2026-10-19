from importlib.metadata import version

import subeventually_core


def test_core_exposes_installed_version() -> None:
    assert subeventually_core.__version__
    assert subeventually_core.__version__ == version("subeventually-core")
