"""Unit tests for pathroot."""

from contextlib import contextmanager
from pathlib import Path

import pytest

import pathroot

# Dictionary of test files to create in root_folder.
# Keys should be Path objects, and values should be None
# for directories, or a bytes object for contents.
TEST_FILES = {
    Path("d1"): None,
    Path("d1/f1.txt"): b"First file",
    Path("d2"): None,
    Path("d2/f2.txt"): b"Second file",
}


# region Fixtures
@pytest.fixture
def root_folder(tmp_path) -> Path:  # type: ignore
    """Self cleaning test folder, populated by TEST_FILES."""
    for p, c in TEST_FILES.items():
        p = tmp_path / p
        if c is None:
            p.mkdir(exist_ok=True, parents=True)
        else:
            p.parent.mkdir(exist_ok=True, parents=True)
            p.write_bytes(c)

    yield tmp_path

    for p in sorted(tmp_path.rglob("*"), reverse=True):
        if p.is_symlink() or p.is_file():
            p.unlink()
        elif p.is_dir():
            p.rmdir()


@contextmanager
def fix_os_name(v: str):
    """Context manager for replacing pathroot.OS_NAME temporarily.

    Args:
        v: Value to set OS_NAME to.
    """
    old_val = pathroot.OS_NAME
    pathroot.OS_NAME = v
    try:
        yield
    finally:
        pathroot.OS_NAME = old_val


@pytest.fixture
def _force_nt():
    """Force the OS name to nt (for Windows)."""
    with fix_os_name("nt"):
        yield


@pytest.fixture
def _force_posix():
    """Force the OS name to darwin (for POSIX)."""
    with fix_os_name("darwin"):
        yield


# endregion


# region Tests
@pytest.mark.usefixtures("_force_nt")
def test_new_windows(root_folder):
    """Test that PathRoot, on Windows, returns a WindowsPathRoot instance."""
    # Act
    r = pathroot.PathRoot(root_folder)

    # Assert
    assert type(r) is pathroot.WindowsPathRoot


@pytest.mark.usefixtures("_force_posix")
def test_new_posix(root_folder):
    """Test that PathRoot, on a POSIX OS, returns a PosixPathRoot instance."""
    # Act
    r = pathroot.PathRoot(root_folder)

    # Assert
    assert type(r) is pathroot.PosixPathRoot


def test_joinpath_works(root_folder):
    """Test that when we use joinpath with a path inside the the root, it works, and we get a PathRoot instance."""
    # Arrange
    r = pathroot.PathRoot(root_folder)

    # Act
    p1 = r.joinpath("foo/bar.txt")

    # Assert
    assert isinstance(p1, pathroot.PathRoot)
    assert p1.safe_root is r.safe_root


def test_joinpath_errors(root_folder):
    """Test that when we use joinpath with a path outside the root, it raises a PathOutsideRootError."""
    # Arrange
    r = pathroot.PathRoot(root_folder)

    # Act and Assert
    with pytest.raises(pathroot.PathOutsideRootError):
        r.joinpath("..", "..", "etc")


def test_divide_works(root_folder):
    """Test that when we use the divide operator inside the root, it works, and we get a PathRoot instance."""
    # Arrange
    r = pathroot.PathRoot(root_folder)

    # Act
    p1 = r / "foo" / "bar.txt"

    # Assert
    assert isinstance(p1, pathroot.PathRoot)
    assert p1.safe_root is r.safe_root


def test_divide_errors(root_folder):
    """Test that when we use the divide operator outside the root, it raises a PathOutsideRootError."""
    # Arrange
    r = pathroot.PathRoot(root_folder)

    # Act and Assert
    with pytest.raises(pathroot.PathOutsideRootError):
        r / ".." / ".." / "etc"


def test_with_segments_works(root_folder):
    """Test that with_segments with a path inside the root works, and we get a PathRoot instance."""
    # Arrange
    r = pathroot.PathRoot(root_folder)

    # Act
    p1 = r.with_segments(root_folder, "foo/bar.txt")

    # Assert
    assert isinstance(p1, pathroot.PathRoot)
    assert p1.safe_root is r.safe_root


def test_with_segments_errors(root_folder):
    """Test that when we use with_segments with a path inside the the root, it works, and we get a PathRoot instance."""
    # Arrange
    r = pathroot.PathRoot(root_folder)

    # Act and Assert
    with pytest.raises(pathroot.PathOutsideRootError):
        r.with_segments(root_folder, "..", "..", "etc")


# TODO: Add tests...
# def test_rename_works(root_folder):
# def test_rename_errors(root_folder):
# def test_replace_works(root_folder):
# def test_replace_errors(root_folder):

# TODO: Other corner cases?
# endregion
