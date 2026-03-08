# PathRoot

## Purpose

PathRoot is a Python library that provides a secure way to work with filesystem paths. It extends Python's `pathlib.Path` to prevent directory traversal attacks by restricting all path operations to a trusted root directory. This is particularly useful when:

- Building applications that handle user-provided file paths
- Creating systems that need to prevent access outside a designated directory
- Implementing sandboxed file access in web applications or APIs
- Ensuring path safety without manual validation checks

## Installation

You can install PathRoot using pip:

```bash
pip install pathroot
```

PathRoot requires Python 3.12 or higher and has no external dependencies.

## How to Use PathRoot

### Basic Usage

Initialize a `PathRoot` object with a path and optional `safe_root` parameter:

```python
from pathroot import PathRoot

# Initialize with explicit safe_root
root = PathRoot('/Users/foo/bar', safe_root='/Users/foo/bar')

# Or initialize without safe_root (defaults to the path itself)
root = PathRoot('/Users/foo/bar')
```

### Path Operations

Once initialized, you can use `PathRoot` like any standard `pathlib.Path` object:

```python
from pathroot import PathRoot

root = PathRoot('/Users/foo/bar')

# Safe operations within the root
my_file = root / 'groceries.txt'  # Works fine
config = root / 'config' / 'settings.json'  # Works fine
```

### Security Protection

PathRoot automatically prevents directory traversal attacks by raising a `PathOutsideRootError` exception:

```python
from pathroot import PathRoot

root = PathRoot('/Users/foo/bar')

# This raises PathOutsideRootError - attempting to traverse outside the root
my_file = root / '..' / '..' / 'groceries.txt'
```

### Features

- Full `pathlib.Path` compatibility for all safe operations
- Automatic validation of all path operations
- Prevents directory traversal exploits
- No external dependencies
- Type-safe with Python 3.10+

## Error Handling

When a path operation would traverse outside the trusted root, PathRoot raises a `PathOutsideRootError` exception. Always catch and handle this exception when working with untrusted paths:

```python
from pathroot import PathRoot, PathOutsideRootError

root = PathRoot('/Users/foo/bar')

try:
    unsafe_path = root / user_input
except PathOutsideRootError:
    # Handle the error - the path would have escaped the root
    print("Invalid path: traversal outside root directory")
```
