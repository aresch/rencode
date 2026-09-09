# AGENTS.md

Welcome! This document outlines development guidelines, architectural decisions, and build conventions for AI agents working on `rencode`.

## Environment & Tooling

- **Package Manager**: Use `uv` for all local environment and build workflows.
- **Python Compatibility**: Python >= 3.9.

### Common Commands
- **Install & Sync Environment**: `uv sync --all-groups` (compiles the Cython extension in editable mode and installs dev tools into `.venv`)
- **Run Tests**: `uv run pytest`
- **Build Distributions**: `uv build`
- **Lint / Format**: `uv run black rencode tests`

---

## Build System & Packaging Rules

1. **Never create a `build.py` in the root directory**:
   - PyPA PEP 517 frontends (`python -m build`) add the current directory to `sys.path`. A root `build.py` shadows the standard `build` library and breaks packaging (Issue #42).
2. **Build Backend**:
   - Uses `setuptools.build_meta` + `cython` declared in `pyproject.toml`.
   - `setup.py` exists solely to invoke `cythonize(Extension("rencode._rencode", ...))`.
3. **Compiler Flags**:
   - Do **not** hardcode CPU-specific optimization flags (e.g. `-march=native`, `-msse`, `-mfma`) in `setup.py`. Compilers and distributors must be allowed to supply their own `CFLAGS` so wheels remain portable across x86, ARM, and Apple Silicon.
4. **PEP 621 / PEP 639 License Rules**:
   - `pyproject.toml` uses SPDX expression `license = "GPL-3.0-only"`.
   - Do **not** add `License :: OSI Approved :: ...` to `classifiers`, as modern setuptools disallows redundant license classifiers when a license expression is present.
5. **Distribution Hygiene**:
   - Binary wheels (`.whl`) must exclude `*.c` and `*.pyx` (configured in `[tool.setuptools.exclude-package-data]`).
   - Source distributions (`.tar.gz`) must include `_rencode.pyx`, `SPEC.md`, `README.md`, `COPYING`, and tests (configured in `MANIFEST.in`).

---

## Architecture & Codebase Details

- `rencode/_rencode.pyx`: The Cython-optimized implementation of the rencode serialization algorithm.
- `rencode/rencode_orig.py`: Pure-Python fallback implementation.
- `rencode/__init__.py`: Attempts to load the compiled `_rencode` extension, falling back to `rencode_orig` if compiled binaries are unavailable.
- **Wire Format & Serialization Behavior**:
  - `loads()` returns strings as `bytes` unless `decode_utf8=True` is provided.
  - Lists in Python serialize to sequence structures that decode as tuples.
  - Full wire format specification is documented in `SPEC.md`.

---

## CI & Automated Release Pipeline

- `.github/workflows/ci.yml`: Runs tests via `uv` across Python 3.9–3.13 on Linux, macOS, and Windows.
- `.github/workflows/wheels.yml`: Uses `cibuildwheel` to compile binary wheels for manylinux (x86_64, aarch64, i686), macOS (arm64, x86_64), and Windows, publishing to PyPI on release tags (`v*`).
