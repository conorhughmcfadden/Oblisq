"""Stable public import surface for the Oblisq OpenGL rendering core.

Downstream consumers (e.g. navigate) should import from here, not from
oblisq.model.gl_backend directly, so internal module reorganization does
not break their imports.
"""
from oblisq.model.gl_backend import GLVolumeViewBackend

__all__ = ["GLVolumeViewBackend"]
