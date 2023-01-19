from importlib.metadata import version

__version__ = version("dodal")
del version

__all__ = ["__version__"]
