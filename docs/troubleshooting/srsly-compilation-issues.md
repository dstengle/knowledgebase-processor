# Troubleshooting srsly Compilation Issues

## Overview

The `srsly` package is a dependency of spaCy that provides high-performance serialization utilities. It includes C extensions that must be compiled during installation, which can cause issues in certain containerization scenarios.

## Common Issues and Solutions

### Issue 1: Missing Build Tools in Buildpacks

**Symptoms:**
- Build fails with "error: Microsoft Visual C++ 14.0 is required" (Windows)
- Build fails with "gcc: command not found" (Linux)
- Error: "No module named '_srsly'"

**Solution:**
Use the full builder instead of tiny/base builders:

```bash
# Use full builder which includes build-essential
pack build myapp --builder paketobuildpacks/builder:full
```

### Issue 2: Alpine Linux Compatibility

**Symptoms:**
- Segmentation faults at runtime
- "Error loading shared library" messages
- ImportError when importing srsly

**Solution:**
Alpine uses musl libc instead of glibc. Install additional dependencies:

```dockerfile
RUN apk add --no-cache \
    gcc \
    g++ \
    musl-dev \
    linux-headers \
    python3-dev \
    openblas-dev \
    gfortran
```

### Issue 3: Missing Runtime Dependencies

**Symptoms:**
- Application starts but crashes when using spaCy
- "libgomp.so.1: cannot open shared object file"

**Solution:**
Ensure runtime dependencies are installed in the final image:

```dockerfile
# For Debian/Ubuntu based images
RUN apt-get update && apt-get install -y \
    libgomp1 \
    libopenblas0

# For Alpine
RUN apk add --no-cache \
    libgomp \
    openblas
```

### Issue 4: Platform-Specific Wheels

**Symptoms:**
- Build works locally but fails in CI/CD
- "No matching distribution found for srsly"

**Solution:**
Force compilation from source or use platform-specific wheels:

```bash
# Force compilation from source
pip install --no-binary :all: srsly

# Or use platform-specific index
pip install --index-url https://pypi.org/simple/ \
    --extra-index-url https://alpine-wheels.github.io/index \
    srsly
```

## Debugging Steps

### 1. Check Compilation Environment

```bash
# In your build container
python -c "import sysconfig; print(sysconfig.get_config_vars())"
gcc --version
python --version
```

### 2. Verify Installation

```python
# Test srsly installation
try:
    import srsly
    print(f"srsly version: {srsly.__version__}")
    # Test basic functionality
    data = {"test": "data"}
    json_bytes = srsly.json_dumps(data)
    print("srsly is working correctly")
except Exception as e:
    print(f"Error: {e}")
```

### 3. Check Shared Libraries

```bash
# List dependencies
ldd $(python -c "import srsly; print(srsly.__file__)")

# On Alpine
apk info -L py3-srsly
```

## Best Practices

### 1. Use Multi-Stage Builds

Separate build and runtime dependencies:

```dockerfile
# Build stage with all compilation tools
FROM python:3.12 as builder
RUN apt-get update && apt-get install -y build-essential
# ... install packages ...

# Runtime stage with minimal dependencies
FROM python:3.12-slim
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
```

### 2. Cache Dependencies

Use Docker build cache effectively:

```dockerfile
# Copy only dependency files first
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root

# Then copy source code
COPY . .
RUN poetry install
```

### 3. Pre-Built Wheels

Consider maintaining pre-built wheels:

```bash
# Build wheels for your platform
pip wheel --wheel-dir ./wheels srsly spacy

# Use pre-built wheels in Dockerfile
COPY wheels/ /tmp/wheels/
RUN pip install --find-links /tmp/wheels srsly spacy
```

### 4. Use Compatible Base Images

Recommended base images:
- `python:3.12-slim-bookworm` (Debian-based, good compatibility)
- `python:3.12` (Full Python image with build tools)
- Avoid `python:3.12-alpine` unless you need the smaller size

## Alternative Solutions

### 1. Use Conda/Mamba

Conda provides pre-compiled binaries:

```dockerfile
FROM continuumio/miniconda3
RUN conda install -c conda-forge spacy
```

### 2. Use Pre-Built Images

Consider using images with spaCy pre-installed:

```dockerfile
FROM explosion/spacy:latest
```

### 3. Build Custom Base Image

Create a base image with all dependencies:

```dockerfile
# base.Dockerfile
FROM python:3.12-slim
RUN apt-get update && apt-get install -y [all-deps]
RUN pip install spacy srsly
```

## CI/CD Considerations

### GitHub Actions

```yaml
- name: Set up Python
  uses: actions/setup-python@v4
  with:
    python-version: '3.12'
    
- name: Install system dependencies
  run: |
    sudo apt-get update
    sudo apt-get install -y build-essential

- name: Install Python dependencies
  run: |
    pip install poetry
    poetry install
```

### GitLab CI

```yaml
before_script:
  - apt-get update && apt-get install -y build-essential
  - pip install poetry
  - poetry install
```

## References

- [srsly GitHub Repository](https://github.com/explosion/srsly)
- [spaCy Installation Guide](https://spacy.io/usage)
- [Cloud Native Buildpacks Python Guide](https://paketo.io/docs/howto/python/)
- [Alpine Linux Python Packages](https://pkgs.alpinelinux.org/packages?name=py3-*)