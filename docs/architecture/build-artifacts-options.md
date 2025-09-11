# Knowledge Base Processor - Build Artifact Options

## Executive Summary

This document explores various build artifact options for the knowledgebase-processor project, with special consideration for the `srsly` compilation issue encountered with cloud native buildpacks. The `srsly` package is a dependency of spaCy and requires compilation of C extensions, which can be problematic in certain containerization approaches.

## Current State

### Dependencies
- Python 3.12
- Poetry for dependency management
- spaCy (which depends on srsly, blis, and other C extensions)
- No existing Dockerfile
- docker-compose.yml only contains Fuseki service

### The srsly Compilation Issue

The `srsly` package (a serialization library used by spaCy) includes C extensions that need to be compiled during installation. This causes issues with:
1. Cloud Native Buildpacks that may not have required build tools
2. Alpine-based images lacking necessary headers/libraries
3. Multi-stage builds where build dependencies aren't properly handled

## Build Artifact Options

### Option 1: Traditional Dockerfile with Multi-Stage Build

**Pros:**
- Full control over build environment
- Can optimize final image size
- Explicit dependency management
- Easy to debug

**Cons:**
- Requires manual maintenance
- More complex than buildpacks

**Implementation:**

```dockerfile
# Build stage
FROM python:3.12-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install poetry
RUN pip install poetry

# Copy project files
WORKDIR /app
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root --only main

# Runtime stage
FROM python:3.12-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application
WORKDIR /app
COPY src/ ./src/
COPY pyproject.toml ./

# Install the application
RUN pip install -e .

CMD ["kb", "--help"]
```

### Option 2: Cloud Native Buildpacks with Custom Builder

**Pros:**
- Automated dependency detection
- Security patches automatically applied
- Follows best practices
- Reproducible builds

**Cons:**
- Less control over build process
- srsly compilation issues
- Larger images

**Solutions for srsly issue:**

1. **Use Paketo Full Builder:**
```bash
pack build knowledgebase-processor \
  --builder paketobuildpacks/builder:full \
  --env BP_CPYTHON_VERSION="3.12.*"
```

2. **Create project.toml with build dependencies:**
```toml
[[build.env]]
name = "BP_CPYTHON_VERSION"
value = "3.12.*"

[[build.env]]
name = "BP_POETRY_VERSION"
value = "1.8.*"

[[build.buildpacks]]
uri = "gcr.io/paketo-buildpacks/python"

[build]
exclude = [
  "tests/",
  "docs/",
  "*.md",
  ".git/"
]
```

3. **Pre-compile wheels approach:**
Create a custom buildpack extension that includes pre-compiled wheels for srsly and other C extensions.

### Option 3: Distroless Images with Bazel

**Pros:**
- Minimal attack surface
- Reproducible builds
- Efficient caching
- Handles C extensions well

**Cons:**
- Steep learning curve
- Complex setup
- Less common in Python ecosystem

**Implementation approach:**
```python
# BUILD.bazel
py_binary(
    name = "kb",
    srcs = ["src/knowledgebase_processor/cli/main.py"],
    deps = [
        requirement("spacy"),
        requirement("srsly"),
        # ... other deps
    ],
)

container_image(
    name = "kb_image",
    base = "@distroless_python3//image",
    entrypoint = ["/kb"],
    files = [":kb"],
)
```

### Option 4: Nix-based Builds

**Pros:**
- Reproducible builds
- Handles C dependencies excellently
- Can generate Docker images
- Declarative configuration

**Cons:**
- Nix learning curve
- Less mainstream

**Implementation:**
```nix
# flake.nix
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    poetry2nix.url = "github:nix-community/poetry2nix";
  };

  outputs = { self, nixpkgs, poetry2nix }: 
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
      poetry2nixLib = poetry2nix.lib.mkPoetry2Nix { inherit pkgs; };
    in {
      packages.${system}.default = poetry2nixLib.mkPoetryApplication {
        projectDir = self;
        preferWheels = true;
      };
      
      dockerImage = pkgs.dockerTools.buildLayeredImage {
        name = "knowledgebase-processor";
        contents = [ self.packages.${system}.default ];
        config.Cmd = [ "kb" ];
      };
    };
}
```

### Option 5: Pre-built Wheels Strategy

**Pros:**
- Avoids compilation entirely
- Fast builds
- Works with any containerization approach

**Cons:**
- Requires wheel repository
- Platform-specific wheels needed

**Implementation:**
1. Build wheels on CI for target platforms
2. Host in private PyPI or artifact repository
3. Modify pip/poetry to use pre-built wheels

```dockerfile
FROM python:3.12-slim

# Use pre-built wheels
RUN pip install --index-url https://your-pypi.com/simple \
    --trusted-host your-pypi.com \
    knowledgebase-processor

CMD ["kb"]
```

### Option 6: Using Conda/Mamba

**Pros:**
- Handles C dependencies well
- Pre-compiled packages available
- Cross-platform support

**Cons:**
- Larger images
- Different ecosystem from pip/poetry

**Implementation:**
```dockerfile
FROM continuumio/miniconda3:latest

COPY environment.yml .
RUN conda env create -f environment.yml

SHELL ["conda", "run", "-n", "kb-env", "/bin/bash", "-c"]

COPY . /app
WORKDIR /app
RUN pip install -e .

CMD ["conda", "run", "-n", "kb-env", "kb"]
```

## Recommended Approach

Given the project's requirements and the srsly compilation issue, I recommend:

### Primary: Traditional Dockerfile with Multi-Stage Build (Option 1)
- Provides full control over the build process
- Explicitly handles C compilation requirements
- Can be optimized for size and security
- Easy to debug and maintain

### Secondary: Cloud Native Buildpacks with Full Builder (Option 2)
- Use for standardized CI/CD pipelines
- Requires the full builder (not tiny) for C compilation support
- Consider creating custom buildpack for spaCy dependencies

### Future Consideration: Nix-based Builds (Option 4)
- Excellent for reproducibility
- Handles complex dependencies well
- Consider for long-term migration

## Implementation Steps

1. **Create Dockerfile** (Priority 1)
   - Multi-stage build with explicit C compilation support
   - Optimize for production use
   - Include health checks and security scanning

2. **Add project.toml for Buildpacks** (Priority 2)
   - Configure for Paketo full builder
   - Document buildpack usage

3. **Set up CI/CD Pipeline** (Priority 3)
   - Build and test multiple artifact types
   - Publish to container registry
   - Security scanning integration

4. **Document Build Process** (Priority 4)
   - Build commands
   - Troubleshooting guide
   - Performance optimization tips

## Security Considerations

1. **Base Image Selection**
   - Use official Python images
   - Consider distroless for production
   - Regular security updates

2. **Dependency Scanning**
   - Integrate Trivy or similar
   - Check for CVEs in dependencies
   - Automated security patches

3. **Runtime Security**
   - Non-root user
   - Read-only filesystem where possible
   - Minimal attack surface

## Performance Considerations

1. **Image Size Optimization**
   - Multi-stage builds
   - Remove build dependencies
   - Use slim base images

2. **Build Cache Optimization**
   - Layer caching strategy
   - Dependency caching
   - Parallel builds where possible

3. **Startup Time**
   - Pre-compile Python files
   - Lazy loading of spaCy models
   - Health check optimization

## Conclusion

The srsly compilation issue with cloud native buildpacks is solvable through multiple approaches. The traditional Dockerfile approach provides the most control and is recommended for immediate implementation, while buildpacks can be used with the full builder for standardized deployments. Long-term consideration should be given to more advanced solutions like Nix for better reproducibility and dependency management.