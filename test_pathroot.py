"""Unit tests for pathroot."""

import logging
from contextlib import contextmanager
from pathlib import Path

import pytest

import pathroot

LOG = logging.getLogger(__name__)

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
            LOG.info("** Created dir %s", p)
        else:
            p.parent.mkdir(exist_ok=True, parents=True)
            p.write_bytes(c)
            LOG.info("** Create file %s", p)

    LOG.info("** Returning %s", tmp_path)
    yield tmp_path

    for p in sorted(tmp_path.rglob("*"), reverse=True):
        if p.is_symlink() or p.is_file():
            p.unlink()
            LOG.info("** Unlinking %s", p)
        elif p.is_dir():
            p.rmdir()
            LOG.info("** Removing dir %s", p)


@contextmanager
def fix_os_name(v: str):
    """Context manager for replacing pathroot.OS_NAME temporarily.

    Args:
        v: Value to set OS_NAME to.
    """
    old_val = pathroot.OS_NAME
    pathroot.OS_NAME = v
    LOG.info("** Set OS_NAME to %r", v)
    try:
        yield
    finally:
        pathroot.OS_NAME = old_val
        LOG.info("** Set OS_NAME back to %r", old_val)


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


def test_rename_works(root_folder):
    """Test that rename works when it should."""
    # Arrange
    p1 = pathroot.PathRoot(root_folder) / "d1"

    # Act
    p2 = p1.rename(root_folder / "d3")

    # Assert
    assert isinstance(p2, pathroot.PathRoot)
    assert p2.safe_root is p1.safe_root


def test_rename_errors(root_folder):
    """Test that rename errors when the target path is outside of the root."""
    # Arrange
    r = pathroot.PathRoot(root_folder)

    # Act and Assert
    with pytest.raises(pathroot.PathOutsideRootError):
        r.rename(root_folder / ".." / ".." / "etc")


def test_replace_works(root_folder):
    """Test that replae works."""
    # Arrange
    p1 = pathroot.PathRoot(root_folder) / "d1"

    # Act
    p2 = p1.replace(root_folder / "d3")

    # Assert
    assert isinstance(p2, pathroot.PathRoot)
    assert p2.safe_root is p1.safe_root


def test_replace_errors(root_folder):
    """Test that replace errors when the target path is outside of the root."""
    # Arrange
    r = pathroot.PathRoot(root_folder)

    # Act and Assert
    with pytest.raises(pathroot.PathOutsideRootError):
        r.replace(root_folder / ".." / ".." / "etc")


# TODO: Other corner cases?
# endregion
