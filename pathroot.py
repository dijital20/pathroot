"""Variant of a Path that does not allow traversal outside of the root."""

from __future__ import annotations

import logging
import os
from pathlib import Path, PosixPath, WindowsPath

LOG = logging.getLogger(__name__)
OS_NAME = os.name


class PathOutsideRootError(OSError):
    """Exception to raise when a path traverses outside a root."""

    def __init__(self, path: Path, root: PathRoot, *args):
        super().__init__(*args)
        self.path = path
        self.root = root

    def __str__(self):
        return f"Path {self.path} ({self.path.resolve()}) is outside of {self.root}."


class PathRoot(Path):
    """Base class for a path that does not allow traversal outside."""

    def __new__(cls, *args, **kwargs):
        if cls is PathRoot:
            cls = WindowsPathRoot if OS_NAME == "nt" else PosixPathRoot
        return object.__new__(cls)

    def __init__(self, *args, safe_root: Path | None = None):
        LOG.debug("Creating new %s from %r with root %r", type(self), args, safe_root)
        super().__init__(*args)

        # If the safe_root is None, then one was not provided. Look through the args
        # and see if we have any PathRoot instances... first one wins.
        if safe_root is None:
            for arg in args:
                if isinstance(arg, PathRoot):
                    safe_root = arg.safe_root
                    break
            else:  # no break
                # Set the safe_root to this path.
                safe_root = Path(self)
        self.safe_root = safe_root

    def __check_path(self, path: Path) -> Path:
        """Check if a path traverses outside of the root path."""
        p = Path(path).resolve()
        if not p.is_relative_to(self.safe_root):
            raise PathOutsideRootError(path, self)

        match path:
            # If the path is a PathRoot with no safe_root set, set it.
            case PathRoot() if path.safe_root is None:
                path.safe_root = self.safe_root

            # If the path is not a PathRoot, make it one.
            case Path() if not isinstance(path, PathRoot):
                path = PathRoot(path, safe_root=self.safe_root)

        return path

    def with_segments(self, *args) -> Path:
        """Return a new path with segments.

        Returns:
            New path.
        """
        LOG.debug("with_segments called with %r", args)
        return self.__check_path(super().with_segments(*args))


class PosixPathRoot(PosixPath, PathRoot):
    """Path that does not allow traversal outside of root for Linux/MacOS."""


class WindowsPathRoot(WindowsPath, PathRoot):
    """Path that does not allow traversal outside of the root for Windows."""
