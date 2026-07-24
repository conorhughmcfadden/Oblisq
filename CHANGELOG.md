# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
(while pre-1.0, breaking changes may occur on minor version bumps).

## [Unreleased]

### Added
- Packaging fixes for PyPI distribution: shader files are now declared as package
  data so they are included in built wheels/sdists.
- `oblisq.gl_backend` public re-export shim as the stable import surface for
  downstream consumers (e.g. `navigate`), instead of reaching into
  `oblisq.model.gl_backend` directly.
- `[app]` optional-dependencies extra bundling the standalone-viewer-only
  dependencies (`tifffile`, `tkinterdnd2`, `dask`, `zarr`, `imagecodecs`,
  `cpp-tiff`), separate from the minimal core (`numpy`, `PyOpenGL`, `glfw`, `PyGLM`).
- Import-isolation tests confirming `oblisq.gl_backend` imports cleanly without any
  `[app]`-only dependency installed.
- GitHub Actions CI (Python 3.9 and 3.11, Ubuntu and Windows).

### Changed
- Lowered `requires-python` from `>=3.11` to `>=3.9` — nothing in the core rendering
  backend requires newer Python versions.
- Unpinned `tifffile` (previously `>=2026`).
- Moved `cpp-tiff` from a hard dependency to the `[app]` extra, matching its existing
  soft-optional runtime handling.

## [0.1.0]
- Initial standalone split from the `navigate` project.
