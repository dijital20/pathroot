"""Variant of a Path that does not allow traversal outside of the root."""

from __future__ import annotations

import logging
import os
from pathlib import Path, PosixPath, WindowsPath

LOG = logging.getLogger(__name__)
OS_NAME = os.name


class PathOutsideRootError(OSError):
    """Exception to raise when a path traverses outside a root."""

    def __init__(self, path: Path, root: Path, *args):
        """Prepare a PathOutsideRootError for use.

        Args:
            path: Target path.
            root: Trusted root path.
            *args: Arguments passed to OSError.
        """
        super().__init__(*args)
        self.path = path
        self.root = root

    def __str__(self) -> str:
        """String message."""
        return f"Path {self.path} ({self.path.resolve()}) is outside of {self.root}."


class PathRoot(Path):
    """Base class for a path that does not allow traversal outside.

    Notes:
        When a PathRoot is first instantiated, if a `safe_root` is not provided, then
        the current directory is used as the SafeRoot. All methods that mutate the path
        or work off of additional provided paths have those paths resolved and checked
        against the safe root. If the resolved path is not relative to the safe root,
        then a `PathOutsideRootError` is raised.
    """

    def __new__(cls, *args, **kwargs) -> WindowsPathRoot | PosixPathRoot:  # noqa: ARG004
        """Generate the OS-specific subclass based on the current OS."""
        if cls is PathRoot:
            cls = WindowsPathRoot if OS_NAME == "nt" else PosixPathRoot
        return object.__new__(cls)

    def __init__(
        self,
        *args,
        safe_root: Path | None = None,
    ):
        """Prepare a PathRoot for use.

        Args:
            *args: Path segments, passed to Path.
            safe_root: Root path to use for all operations. Defaults to None (current path is used).
        """
        super().__init__(*args)

        # If the safe_root is None, then one was not provided. Look through the args
        # and see if we have any PathRoot instances... first one wins.
        match safe_root:
            case bytes():
                # Accept bytes by decoding using UTF-8
                self.__safe_root = Path(safe_root.decode("UTF-8")).resolve()

            case str():
                self.__safe_root = Path(safe_root).resolve()

            case os.PathLike():
                self.__safe_root = Path(os.fspath(safe_root)).resolve()

            case _:
                for arg in args:
                    if isinstance(arg, PathRoot):
                        self.__safe_root = arg.safe_root
                        break

                else:  # no break
                    # Set the safe_root to this path.
                    self.__safe_root = Path(self).resolve()
                    LOG.debug("No safe root given, using %r", self.__safe_root)

        LOG.debug("Created %r", self)

    @property
    def safe_root(self) -> Path:
        """Get the safe root path.

        Returns:
            The trusted root path.
        """
        return self.__safe_root

    def __repr__(self) -> str:
        """Internal string representation."""
        return f"{type(self).__name__}({self.as_posix()!r}, safe_root={self.safe_root.as_posix()!r})"

    def __check_path(
        self,
        path: PathRoot | os.PathLike[str] | os.PathLike[bytes] | str | bytes,
    ) -> PathRoot:
        """Check if a path traverses outside.

        Args:
            path: Path to check.

        Returns:
            The tested path.

        Raises:
            PathOutsideRootError: If the path traverses outside of the root path.
        """
        # Normalize input into a resolved pathlib.Path using structural pattern matching
        match path:
            case bytes():
                p = Path(path.decode("UTF-8")).resolve()

            case str():
                p = Path(path).resolve()

            case os.PathLike():
                p = Path(os.fspath(path)).resolve()

            case _:
                msg = f"Unsupported path type: {type(path)!r}"
                raise TypeError(msg)

        LOG.debug("Testing %r against %r", p, self.safe_root)
        if not p.is_relative_to(self.safe_root):
            raise PathOutsideRootError(p, self.safe_root)

        # Preserve the runtime subclass when returning a PathRoot-like object
        return type(self)(p, safe_root=self.safe_root)

    def with_segments(self, *args) -> PathRoot:
        """Return a new path with segments.

        Args:
            *args: Path segments.

        Returns:
            New path.
        """
        # Build a Path from the provided segments and validate it.
        p = Path(*args)
        return self.__check_path(p)

    def rename(
        self,
        target: os.PathLike[str] | str,
    ) -> PathRoot:
        """Rename this path to the target path.

        Args:
            target: Target path. Must be in the root.

        Returns:
            New PathRoot instance pointing to the target path.

        Notes:
            The target path may be absolute or relative. Relative paths are
            interpreted relative to the current working directory *not* the
            directory of the Path object.
        """
        result = super().rename(self.__check_path(target))
        return type(self)(result, safe_root=self.safe_root)

    def replace(
        self,
        target: os.PathLike[str] | str,
    ) -> PathRoot:
        """Rename this path to the target path, overwriting if that path exists.

        Args:
            target: Target path. Must be in the root.

        Returns:
            New PathRoot instance pointing to the target path.

        Notes:
            The target path may be absolute or relative. Relative paths are
            interpreted relative to the current working directory *not* the
            directory of the Path object.
        """
        result = super().replace(self.__check_path(target))
        return type(self)(result, safe_root=self.safe_root)

    def symlink_to(
        self,
        target: os.PathLike[str] | os.PathLike[bytes] | str | bytes,
        target_is_directory: bool = False,
    ) -> None:
        """Make this path a symlink pointing to the target path.

        Args:
            target: Target to link to. Must be inside root path.
            target_is_directory: Should the target be treated as a directory (only valid for Windows). Defaults to False.
        """
        return super().symlink_to(self.__check_path(target), target_is_directory)

    def hardlink_to(
        self,
        target: os.PathLike[str] | os.PathLike[bytes] | str | bytes,
    ) -> None:
        """Make this path a hard link pointing to the same file as *target*.

        Args:
            target: Target to link to. Must be inside the root path.
        """
        return super().hardlink_to(self.__check_path(target))


class PosixPathRoot(PosixPath, PathRoot):
    """Path that does not allow traversal outside of root for Linux/MacOS."""

    def __new__(cls, *args, **kwargs):  # noqa: ARG004
        """Bypass PosixPath's platform guard and delegate to object.__new__."""
        return object.__new__(cls)


class WindowsPathRoot(WindowsPath, PathRoot):
    """Path that does not allow traversal outside of the root for Windows."""

    def __new__(cls, *args, **kwargs):  # noqa: ARG004
        """Bypass WindowsPath's platform guard and delegate to object.__new__."""
        return object.__new__(cls)
