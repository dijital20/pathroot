"""Unit tests for pathroot."""

import logging
import pathlib
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
    pathroot.OS_NAME = v  # ty:ignore[invalid-assignment]
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


# region Tests - OS-Specific Construction
@pytest.mark.usefixtures("_force_nt")
def test_new_windows(root_folder):
    """Test that PathRoot on Windows returns a WindowsPathRoot instance."""
    # Arrange (OS_NAME is set to "nt" by _force_nt fixture)

    # Act
    r = pathroot.PathRoot(root_folder)

    # Assert
    assert type(r) is pathroot.WindowsPathRoot


@pytest.mark.usefixtures("_force_posix")
def test_new_posix(root_folder):
    """Test that PathRoot on POSIX OS returns a PosixPathRoot instance."""
    # Arrange (OS_NAME is set to "darwin" by _force_posix fixture)

    # Act
    r = pathroot.PathRoot(root_folder)

    # Assert
    assert type(r) is pathroot.PosixPathRoot


# endregion


# region Tests - Path Operations (Success Cases)
def test_joinpath_works(root_folder):
    """Test joinpath with path inside root works and returns PathRoot."""
    # Arrange
    r = pathroot.PathRoot(root_folder)

    # Act
    p1 = r.joinpath("foo/bar.txt")

    # Assert
    assert isinstance(p1, pathroot.PathRoot)
    assert p1.safe_root == r.safe_root


def test_divide_works(root_folder):
    """Test divide operator inside root works and returns PathRoot."""
    # Arrange
    r = pathroot.PathRoot(root_folder)

    # Act
    p1 = r / "foo" / "bar.txt"

    # Assert
    assert isinstance(p1, pathroot.PathRoot)
    assert p1.safe_root == r.safe_root


def test_with_segments_works(root_folder):
    """Test with_segments inside root works and returns PathRoot."""
    # Arrange
    r = pathroot.PathRoot(root_folder)

    # Act
    p1 = r.with_segments(root_folder, "foo/bar.txt")

    # Assert
    assert isinstance(p1, pathroot.PathRoot)
    assert p1.safe_root == r.safe_root


def test_rename_works(root_folder):
    """Test rename works and returns PathRoot with same safe_root."""
    # Arrange
    p1 = pathroot.PathRoot(root_folder) / "d1"

    # Act
    p2 = p1.rename(root_folder / "d3")

    # Assert
    assert isinstance(p2, pathroot.PathRoot)
    assert p2.safe_root == p1.safe_root


def test_replace_works(root_folder):
    """Test replace works and returns PathRoot with same safe_root."""
    # Arrange
    p1 = pathroot.PathRoot(root_folder) / "d1"

    # Act
    p2 = p1.replace(root_folder / "d3")

    # Assert
    assert isinstance(p2, pathroot.PathRoot)
    assert p2.safe_root == p1.safe_root


def test_safe_root_inherits_from_pathroot_argument(tmp_path):
    """Test that new PathRoot inherits safe_root from PathRoot arg."""
    # Arrange
    parent = pathroot.PathRoot(tmp_path)

    # Act
    child = pathroot.PathRoot(parent, "subdir")

    # Assert
    assert child.safe_root == parent.safe_root
    assert isinstance(child, pathroot.PathRoot)


def test_rename_accepts_bytes_target_and_moves_file(tmp_path):
    """Test rename accepts bytes target and moves file inside root."""
    # Arrange
    root = tmp_path
    src = root / "a.txt"
    dst = root / "b.txt"
    content = b"hello"
    src.write_bytes(content)
    pr_file = pathroot.PathRoot(root) / "a.txt"
    target_bytes = str(dst).encode("utf-8")

    # Act
    new_path = pr_file.rename(target_bytes)

    # Assert
    assert isinstance(new_path, pathroot.PathRoot)
    assert new_path.exists()
    assert dst.read_bytes() == content


# endregion


# region Tests - PathOutsideRootError
def test_joinpath_errors(root_folder):
    """Test joinpath raises PathOutsideRootError for paths outside root."""
    # Arrange
    r = pathroot.PathRoot(root_folder)

    # Act and Assert
    with pytest.raises(pathroot.PathOutsideRootError):
        r.joinpath("..", "..", "etc")


def test_divide_errors(root_folder):
    """Test divide operator raises PathOutsideRootError for outside paths."""
    # Arrange
    r = pathroot.PathRoot(root_folder)

    # Act and Assert
    with pytest.raises(pathroot.PathOutsideRootError):
        r / ".." / ".." / "etc"


def test_with_segments_errors(root_folder):
    """Test with_segments raises PathOutsideRootError for outside paths."""
    # Arrange
    r = pathroot.PathRoot(root_folder)

    # Act and Assert
    with pytest.raises(pathroot.PathOutsideRootError):
        r.with_segments(root_folder, "..", "..", "etc")


def test_rename_errors(root_folder):
    """Test rename raises PathOutsideRootError for outside paths."""
    # Arrange
    r = pathroot.PathRoot(root_folder)

    # Act and Assert
    with pytest.raises(pathroot.PathOutsideRootError):
        r.rename(root_folder / ".." / ".." / "etc")


def test_replace_errors(root_folder):
    """Test replace raises PathOutsideRootError for outside paths."""
    # Arrange
    r = pathroot.PathRoot(root_folder)

    # Act and Assert
    with pytest.raises(pathroot.PathOutsideRootError):
        r.replace(root_folder / ".." / ".." / "etc")


def test_pathoutsiderooterror_str_contains_paths(tmp_path):
    """Test PathOutsideRootError string contains path and safe root."""
    # Arrange
    root = tmp_path
    pr = pathroot.PathRoot(root)

    # Act and Assert
    with pytest.raises(pathroot.PathOutsideRootError) as excinfo:
        pr.joinpath("..", "..", "outside")

    # Assert
    err = excinfo.value
    s = str(err)
    assert "is outside of" in s
    assert str(err.path.resolve()) in s
    assert str(err.root) in s


def test_symlink_to_raises_for_outside_target(tmp_path):
    """Test symlink_to raises PathOutsideRootError for outside target."""
    # Arrange
    root = tmp_path
    pr = pathroot.PathRoot(root)
    outside = root / ".." / "etc"

    # Act and Assert
    with pytest.raises(pathroot.PathOutsideRootError):
        pr.symlink_to(outside)


def test_hardlink_to_raises_for_outside_target(tmp_path):
    """Test hardlink_to raises PathOutsideRootError for outside target."""
    # Arrange
    root = tmp_path
    pr = pathroot.PathRoot(root)
    outside = root / ".." / "etc"

    # Act and Assert
    with pytest.raises(pathroot.PathOutsideRootError):
        pr.hardlink_to(outside)


# endregion


# region Tests - Link Methods (Success Cases)
def test_symlink_to_accepts_bytes_target_and_preserves_safe_root(monkeypatch, tmp_path):
    """Test symlink_to accepts bytes and passes PathRoot to super."""
    # Arrange
    root = tmp_path
    (root / "target.txt").write_bytes(b"x")
    pr_link = pathroot.PathRoot(root) / "link"
    target_bytes = str(root / "target.txt").encode("utf-8")
    recorded = {}

    def fake_symlink_to(self, target, target_is_directory=False):
        recorded["self"] = self
        recorded["target"] = target
        recorded["target_is_directory"] = target_is_directory
        return None

    monkeypatch.setattr(pathlib.Path, "symlink_to", fake_symlink_to, raising=True)

    # Act
    pr_link.symlink_to(target_bytes, target_is_directory=False)

    # Assert
    assert "target" in recorded
    target_passed = recorded["target"]
    assert isinstance(target_passed, pathroot.PathRoot)
    assert target_passed.safe_root == pr_link.safe_root


def test_hardlink_to_accepts_bytes_target_and_calls_super(monkeypatch, tmp_path):
    """Test hardlink_to accepts bytes and passes PathRoot to super."""
    # Arrange
    root = tmp_path
    (root / "target.txt").write_bytes(b"x")
    pr_link = pathroot.PathRoot(root) / "linkfile"
    target_bytes = str(root / "target.txt").encode("utf-8")
    recorded = {}

    def fake_hardlink_to(self, target):
        recorded["self"] = self
        recorded["target"] = target
        return None

    monkeypatch.setattr(pathlib.Path, "hardlink_to", fake_hardlink_to, raising=False)

    # Act
    pr_link.hardlink_to(target_bytes)

    # Assert
    assert "target" in recorded
    target_passed = recorded["target"]
    assert isinstance(target_passed, pathroot.PathRoot)
    assert target_passed.safe_root == pr_link.safe_root


# endregion


# region Tests - Actual Link Creation (Edge Cases)
def test_symlink_to_creates_link_for_inside_target(tmp_path):
    """Test that symlink_to actually creates a link when target is inside root."""
    # Arrange
    root = tmp_path
    target = root / "inside.txt"
    target.write_bytes(b"inside")
    link = pathroot.PathRoot(root) / "mylink"

    # Act
    link.symlink_to(target)

    # Assert
    assert link.exists()
    assert link.is_symlink()
    # reading via the symlink should give the same bytes
    assert (root / "mylink").read_bytes() == b"inside"


def test_symlink_to_rejects_actual_outside_target(tmp_path):
    """Test that symlink_to raises when target is an actual file outside the root."""
    # Arrange
    root = tmp_path
    outside_dir = tmp_path.parent / (tmp_path.name + "_outside")
    outside_dir.mkdir(exist_ok=True)
    outside_file = outside_dir / "outside.txt"
    outside_file.write_bytes(b"outside")

    pr = pathroot.PathRoot(root)
    link = pr / "badlink"

    # Act / Assert
    with pytest.raises(pathroot.PathOutsideRootError):
        link.symlink_to(outside_file)


def test_hardlink_to_rejects_actual_outside_target(tmp_path):
    """Test that hardlink_to raises when target is an actual file outside the root."""
    # Arrange
    root = tmp_path
    outside_dir = tmp_path.parent / (tmp_path.name + "_outside_hl")
    outside_dir.mkdir(exist_ok=True)
    outside_file = outside_dir / "outside_hl.txt"
    outside_file.write_bytes(b"outside-hl")

    pr = pathroot.PathRoot(root)
    link = pr / "badhardlink"

    # Act / Assert
    with pytest.raises(pathroot.PathOutsideRootError):
        link.hardlink_to(outside_file)


# endregion
