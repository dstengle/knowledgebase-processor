# ADR-0011: Integration Testing with Jena Fuseki

## ADR-0011: Running Jena Fuseki in Docker for Integration Testing

**Date:** 2025-01-20

**Status:** Proposed

## Context

The knowledgebase-processor project requires integration testing with a SPARQL endpoint to validate the RDF conversion and query functionality. Currently, the project has:

- A `docker-compose.yml` file that already defines a Fuseki service
- A `fuseki_wrapper.py` module that manages Fuseki server lifecycle for testing
- Integration tests that need a reliable SPARQL endpoint

The existing Docker Compose configuration runs Fuseki but needs to be optimized for integration testing scenarios. The fuseki_wrapper.py currently supports both Docker and standalone modes, but the Docker mode implementation needs to align with the docker-compose service definition for consistency.

Key requirements for integration testing:
- Consistent test environment across different development machines
- Fast startup and teardown for test execution
- Isolated test data that doesn't persist between test runs
- Easy integration with the existing test infrastructure

## Decision

We will use the existing Jena Fuseki service definition in `docker-compose.yml` for integration testing, with the following refinements:

1. The Fuseki service will use an in-memory dataset (`--mem` flag) for faster performance and automatic cleanup
2. The fuseki_wrapper.py will be updated to connect to the Docker Compose service rather than managing its own containers
3. A dedicated test dataset endpoint (`/test`) will be used for all integration tests
4. Health checks will ensure the service is ready before tests run

The service definition in docker-compose.yml will remain as:

```yaml
services:
  fuseki:
    image: stain/jena-fuseki:latest
    ports:
      - "3030:3030"
    environment:
      - ADMIN_PASSWORD=admin
      - JVM_ARGS=-Xmx2g
    volumes:
      - fuseki-data:/fuseki
      - ./data:/staging
    command: ["/jena-fuseki/fuseki-server", "--update", "--mem", "/test"]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3030/$/ping"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

## Rationale

This decision supports our architectural principles:

**Simplicity**: Using Docker Compose provides a single command (`docker-compose up`) to start all required services. The in-memory dataset eliminates complex cleanup procedures.

**Consistency**: All developers and CI environments will use the exact same Fuseki version and configuration, eliminating "works on my machine" issues.

**Integration**: The fuseki_wrapper.py can detect if the Docker Compose service is already running and use it, or start it automatically if needed. This provides flexibility for both manual testing and automated test runs.

**Performance**: The in-memory dataset (`--mem` flag) provides faster test execution compared to persistent storage, which is ideal for integration tests that need fresh data for each test run.

## Alternatives Considered

### 1. Embedded Fuseki Server
- **Approach**: Run Fuseki as an embedded server within the Python process
- **Advantages**: No external dependencies, faster startup
- **Why not chosen**: Fuseki doesn't provide a Python embedding API, would require complex subprocess management

### 2. Separate Docker Container per Test
- **Approach**: Have fuseki_wrapper.py create isolated containers for each test
- **Advantages**: Complete isolation between tests
- **Why not chosen**: Slower test execution due to container startup/teardown overhead, more complex resource management

### 3. Mock SPARQL Endpoint
- **Approach**: Create a mock SPARQL endpoint that simulates Fuseki responses
- **Advantages**: Very fast, no external dependencies
- **Why not chosen**: Doesn't test actual SPARQL query execution, could miss real integration issues

## Consequences

### Positive Consequences

1. **Simplified Setup**: Developers can run integration tests with just `docker-compose up` and `poetry run pytest`
2. **Consistent Environment**: All tests run against the same Fuseki version and configuration
3. **Fast Test Execution**: In-memory dataset provides quick startup and no cleanup overhead
4. **Resource Efficiency**: Single Fuseki instance serves all integration tests
5. **Easy CI Integration**: Docker Compose works well in CI/CD pipelines

### Negative Consequences

1. **Docker Dependency**: Developers must have Docker installed to run integration tests
2. **Port Conflicts**: Port 3030 must be available; conflicts require manual resolution
3. **Shared State Risk**: Tests must be careful to clean up their data to avoid interference
4. **Memory Limitations**: Large test datasets might exceed the allocated 2GB JVM heap

### Mitigation Strategies

- Document Docker installation requirements clearly in the README
- Make the port configurable through environment variables
- Implement proper test isolation with setup/teardown methods that clear data
- Monitor memory usage and adjust JVM_ARGS if needed

## Related Decisions

- **ADR-0009**: Knowledge Graph RDF Store - This decision implements the testing infrastructure for the RDF store chosen in ADR-0009
- **ADR-0005**: Poetry as Package Manager - Integration tests will be run through Poetry scripts
- **ADR-0008**: Flexible Metadata Store - The SPARQL endpoint serves as one implementation of the metadata store interface

## Notes

The fuseki_wrapper.py module should be updated to:
1. Check if the Docker Compose service is already running before attempting to start its own container
2. Use the dataset URL `http://localhost:3030/test` for all operations
3. Provide clear error messages if Docker or the Fuseki service is not available

Future enhancements could include:
- Multiple test datasets for parallel test execution
- Persistent test data volumes for debugging failed tests
- Performance monitoring of SPARQL queries during tests