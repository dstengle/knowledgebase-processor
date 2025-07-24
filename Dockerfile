# Multi-stage build to handle Python dependencies with C extensions
FROM python:3.12-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install poetry
RUN pip install poetry

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Configure poetry to not create virtual environment
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --only=main --no-root

# Production stage
FROM python:3.12-slim as runtime

# Create non-root user
RUN useradd --create-home --shell /bin/bash kbp

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY src/ /app/src/
COPY pyproject.toml README.md /app/

WORKDIR /app

# Install the package
RUN pip install -e .

USER kbp

# Default command
CMD ["kb", "--help"]