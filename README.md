# PathRoot

## What is PathRoot?

A `PathRoot` object is a subclass of `pathlib.Path`. It takes an extra `safe_root=` keyword argument to set a trusted 
root, and prevents operations that traverse outside of the trusted root.

## How do you use PathRoot?

You can initialize a `PathRoot` object like this:

```python
from pathroot import PathRoot

root = PathRoot('/Users/foo/bar', safe_root='/Users/foo/bar')
root = PathRoot('/Users/foo/bar')  # This also works.
```

From there, you can do anything you can do with a `Path` object. For instance:

```python
my_file = root / 'groceries.txt'  # This would work.
my_file = root / '..' / '..' / 'groceries.txt'  # This would raise a `PathOutsideRootError` exception.
```
