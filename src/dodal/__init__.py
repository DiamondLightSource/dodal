from importlib.metadata import version

__version__ = version("python-dodal")
del version

__all__ = ["__version__"]
