"""Unit tests for pathroot."""

from contextlib import contextmanager
from pathlib import Path
import pytest

import pathroot


# region Fixtures
@pytest.fixture
def root_folder(tmp_path) -> Path:
    p = tmp_path
    return p


@contextmanager
def fix_os_name(v: str):
    old_val = pathroot.OS_NAME
    pathroot.OS_NAME = v
    try:
        yield
    finally:
        pathroot.OS_NAME = old_val


@pytest.fixture
def force_nt():
    with fix_os_name("nt"):
        yield


@pytest.fixture
def force_posix():
    with fix_os_name("darwin"):
        yield


# endregion


# region Tests
def test_new_windows(root_folder, force_nt):
    # Act
    r = pathroot.PathRoot(root_folder)

    # Assert
    assert type(r) is pathroot.WindowsPathRoot


def test_new_posix(root_folder, force_posix):
    # Act
    r = pathroot.PathRoot(root_folder)

    # Assert
    assert type(r) is pathroot.PosixPathRoot


def test_joinpath_works(root_folder):
    # Arrange
    r = pathroot.PathRoot(root_folder)

    # Act
    p1 = r.joinpath("foo/bar.txt")

    # Assert
    assert isinstance(p1, pathroot.PathRoot)
    assert p1.safe_root is r.safe_root


def test_joinpath_errors(root_folder):
    # Arrange
    r = pathroot.PathRoot(root_folder)

    # Act and Assert
    with pytest.raises(pathroot.PathOutsideRootError):
        r.joinpath("..", "..", "etc")


def test_divide_works(root_folder):
    # Arrange
    r = pathroot.PathRoot(root_folder)

    # Act
    p1 = r / "foo" / "bar.txt"

    # Assert
    assert isinstance(p1, pathroot.PathRoot)
    assert p1.safe_root is r.safe_root


def test_divide_errors(root_folder):
    # Arrange
    r = pathroot.PathRoot(root_folder)

    # Act and Assert
    with pytest.raises(pathroot.PathOutsideRootError):
        r / ".." / ".." / "etc"


# endregion
