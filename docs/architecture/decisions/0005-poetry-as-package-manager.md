# ADR-0005: Use Poetry as the Package Manager

**Date:** 2025-05-09

**Status:** Accepted

## Context

The project requires a robust and reliable package manager to handle dependencies, manage virtual environments, and ensure reproducible builds. As the project evolves, maintaining a clean and consistent development environment becomes crucial. The current `pyproject.toml` and `poetry.lock` files indicate that Poetry is already in use, and this ADR formalizes that decision.

## Decision

We will use Poetry as the primary package and dependency manager for this Python project.

## Rationale

Poetry offers several advantages that align with the project's needs:

-   **Dependency Resolution:** Poetry has a robust dependency resolver that helps prevent conflicts and ensures that the project's dependencies are compatible.
-   **Integrated Tooling:** It combines dependency management, packaging, and publishing into a single tool, simplifying the development workflow.
-   **`pyproject.toml` Standard:** Poetry uses the `pyproject.toml` file, which is the standard for configuring Python projects, making it future-proof and interoperable with other tools.
-   **Lock File:** The `poetry.lock` file ensures deterministic builds by locking the exact versions of all dependencies, which is critical for reproducibility.
-   **Virtual Environment Management:** Poetry automatically creates and manages virtual environments, isolating project dependencies.
-   **Ease of Use:** It provides a user-friendly command-line interface.

## Alternatives Considered

-   **pip with `requirements.txt`:**
    -   **Description:** The traditional way of managing Python dependencies using `pip` and a `requirements.txt` file.
    -   **Advantages:** Simple for small projects, widely understood.
    -   **Why not selected:** Lacks robust dependency resolution, does not manage virtual environments natively, and can lead to "dependency hell" in complex projects. `requirements.txt` files can also become out of sync with actual dependencies.

-   **Pipenv:**
    -   **Description:** A tool that aims to bring the best of all packaging worlds (bundler, npm, yarn, etc.) to the Python world. It combines `pip` and `virtualenv`.
    -   **Advantages:** Manages `Pipfile` and `Pipfile.lock`, handles virtual environments.
    -   **Why not selected:** While an improvement over `pip` + `requirements.txt`, Poetry's dependency resolver is often considered more robust and faster. Poetry's adoption of `pyproject.toml` is also more aligned with modern Python packaging standards.

-   **Conda:**
    -   **Description:** A cross-platform package and environment manager that can manage packages and dependencies for many languages, but is particularly popular in the data science community for Python.
    -   **Advantages:** Excellent for managing complex data science libraries and non-Python dependencies.
    -   **Why not selected:** Conda is more heavyweight than needed for this project, which is primarily a Python application without extensive non-Python or complex binary dependencies. Poetry is more lightweight and focused on Python packaging.

-   **uv:**
    -   **Description:** An extremely fast Python package installer and resolver, written in Rust, designed as a drop-in replacement for pip and pip-tools.
    -   **Advantages:** Significant speed improvements in dependency resolution and installation, compatibility with `requirements.txt` and `pyproject.toml`.
    -   **Why not selected:** While `uv` offers impressive speed, it is a newer tool. Potential compatibility issues with other tools in the ecosystem, such as cloud-native buildpacks or less common deployment environments, might arise. Poetry provides a more established and comprehensive solution for both dependency management and packaging, which is beneficial for long-term project stability and broader tooling compatibility at this stage.

## Consequences

-   **Positive:**
    -   Improved consistency and reproducibility of builds.
    -   Simplified dependency management.
    -   Clearer project structure with `pyproject.toml` and `poetry.lock`.
    -   Easier onboarding for new developers familiar with Poetry.
-   **Negative:**
    -   Developers need to be familiar with Poetry and its commands.
    -   Slight learning curve for those accustomed to other tools.
-   **Trade-offs:**
    -   We are trading the ubiquity of `pip` for the more advanced features and stricter dependency management of Poetry.

## Related Decisions

-   [ADR-0001: Python as Implementation Language](0001-python-as-implementation-language.md:1) - The choice of Python necessitates a Python package manager.
-   [ADR-0004: Package Structure](0004-package-structure.md:1) - Poetry influences how the package is built and structured.

## Notes

The `CONTEXT_STRING` provided was: `{"component": "build-system", "evolution_plan": "Project Infrastructure"}`. This decision directly impacts the "build-system" component and is part of the "Project Infrastructure" evolution.