from importlib.metadata import version

__version__ = version("dls-dodal")
del version

__all__ = ["__version__"]
