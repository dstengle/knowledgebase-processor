# CLI Performance Testing Guide

This document describes the comprehensive performance testing suite for the Knowledge Base Processor CLI.

## Overview

The CLI performance testing suite includes four main components:

1. **Comprehensive Performance Tests** (`test_cli_performance.py`) - Detailed unittest-based tests
2. **Pytest Benchmark Tests** (`test_cli_benchmarks.py`) - pytest-benchmark based performance tests
3. **Reliability Tests** (`test_cli_reliability.py`) - Error handling and recovery tests
4. **Test Runner** (`run_performance_tests.py`) - Orchestration and reporting

## Test Categories

### 1. Performance Tests

**File**: `tests/cli/test_cli_performance.py`

- **Startup Performance**: CLI startup time measurement
- **File Processing**: Small, medium, and large dataset processing
- **Memory Usage**: Memory consumption and scaling tests
- **Concurrency**: Multiple CLI instance handling
- **Throughput**: Files per second processing rates

**Key Features**:
- Custom `PerformanceMetrics` class for detailed monitoring
- Memory tracking with `psutil`
- CPU usage monitoring
- Benchmark comparison across iterations

### 2. Pytest Benchmark Tests

**File**: `tests/cli/test_cli_benchmarks.py`

- **pytest-benchmark Integration**: Statistical performance analysis
- **Automated Benchmarking**: Consistent performance measurement
- **Memory Benchmarks**: Dedicated memory usage tests
- **Stress Tests**: High-load scenario testing

**Usage**:
```bash
# Run all benchmarks
pytest tests/cli/test_cli_benchmarks.py --benchmark-only

# Run specific benchmark categories
pytest -m benchmark tests/cli/
pytest -m memory tests/cli/
pytest -m stress tests/cli/
```

### 3. Reliability Tests

**File**: `tests/cli/test_cli_reliability.py`

- **Error Handling**: Invalid inputs, malformed files
- **Signal Handling**: SIGINT/SIGTERM graceful shutdown
- **Resource Constraints**: Memory limits, disk space
- **Network Issues**: Timeout handling, connection failures
- **Edge Cases**: Unicode paths, concurrent access

### 4. Test Runner

**File**: `scripts/run_performance_tests.py`

Comprehensive test orchestration with:
- Multiple test suite execution
- Performance report generation
- System information collection
- Issue analysis and reporting

## Running Tests

### Quick Performance Check

```bash
python scripts/run_performance_tests.py --quick
```

### Individual Test Suites

```bash
# Benchmark tests only
python scripts/run_performance_tests.py --benchmark

# Reliability tests
python scripts/run_performance_tests.py --reliability

# Stress tests  
python scripts/run_performance_tests.py --stress

# Memory tests
python scripts/run_performance_tests.py --memory

# Comprehensive tests
python scripts/run_performance_tests.py --comprehensive
```

### All Tests with Report

```bash
python scripts/run_performance_tests.py --all --report performance_report.json
```

### Direct Pytest Usage

```bash
# Basic performance tests
pytest tests/cli/test_cli_performance.py -v

# Benchmark tests with detailed output
pytest tests/cli/test_cli_benchmarks.py --benchmark-only --benchmark-sort=mean

# Reliability tests
pytest tests/cli/test_cli_reliability.py -v

# Run only memory tests
pytest -m memory tests/cli/

# Run with timeout for long tests
pytest tests/cli/ --timeout=600
```

## Performance Metrics

### Measured Metrics

1. **Duration**: Execution time for various operations
2. **Memory Usage**: Peak and delta memory consumption
3. **CPU Usage**: Average CPU utilization during processing
4. **Throughput**: Files processed per second
5. **Startup Time**: Time to CLI initialization
6. **Scaling**: Performance vs. dataset size

### Performance Targets

- **CLI Startup**: < 5 seconds average, < 10 seconds max
- **Small Files (10 files)**: < 30 seconds, > 0.5 files/sec
- **Medium Files (50 files)**: < 120 seconds, > 0.5 files/sec  
- **Memory Usage**: < 100MB for small datasets, < 300MB for medium
- **Memory Scaling**: Should not scale linearly with file count

## Test Data

### Automatically Generated Test Data

The test suite automatically generates various types of test data:

1. **Small Dataset**: 10 simple markdown files
2. **Medium Dataset**: 50 complex markdown files with tables, code blocks, wikilinks
3. **Large Files**: Single files up to 1MB+ with thousands of sections
4. **Malformed Data**: Binary data, invalid Unicode, extremely long lines
5. **Edge Cases**: Empty files, Unicode filenames, deeply nested directories

### Test Data Characteristics

- **Variety**: Different markdown features (headers, lists, code, tables, wikilinks)
- **Scaling**: Consistent structure across different sizes
- **Realistic**: Based on actual knowledge base content patterns
- **Stress Testing**: Extreme cases to test limits

## Continuous Integration

### CI Configuration

Add to your CI pipeline:

```yaml
- name: Install test dependencies
  run: poetry install --with=test

- name: Run performance tests
  run: python scripts/run_performance_tests.py --quick --report ci_performance.json
  timeout-minutes: 30

- name: Upload performance report
  uses: actions/upload-artifact@v3
  with:
    name: performance-report
    path: ci_performance.json
```

### Performance Regression Detection

The test suite includes mechanisms to detect performance regressions:

- **Baseline Comparison**: Compare against previous runs
- **Statistical Analysis**: Coefficient of variation checks
- **Threshold Monitoring**: Automatic failure on performance degradation
- **Trend Analysis**: Long-term performance tracking

## Troubleshooting

### Common Issues

1. **Tests Timeout**: Increase timeout values in pytest.ini or test runner
2. **Memory Errors**: Run tests on system with sufficient RAM (>4GB recommended)
3. **Permission Errors**: Ensure write access to temporary directories
4. **Network Tests Fail**: Check internet connectivity for network-based tests

### Debug Options

```bash
# Verbose output
pytest tests/cli/ -v -s

# Keep temporary files for inspection
pytest tests/cli/ --keep-tmp

# Run single test method
pytest tests/cli/test_cli_performance.py::TestCLIPerformance::test_cli_startup_time -v

# Show benchmark statistics
pytest tests/cli/test_cli_benchmarks.py --benchmark-only --benchmark-verbose
```

### Performance Analysis

If tests are failing due to performance issues:

1. **Check System Load**: Ensure system isn't under heavy load during testing
2. **Review Test Data**: Verify test data generation is appropriate
3. **Monitor Resources**: Use system monitoring tools during test runs
4. **Isolate Issues**: Run individual test methods to identify bottlenecks

## Extending Tests

### Adding New Performance Tests

1. **unittest Style**: Add methods to `TestCLIPerformance` class
2. **pytest-benchmark**: Add methods to `TestCLIBenchmarks` class
3. **Reliability**: Add methods to `TestCLIReliability` class

### Custom Metrics

To add custom performance metrics:

```python
def test_custom_metric(self, benchmark):
    def custom_operation():
        # Your operation here
        result = run_cli_command(["your", "args"])
        return result
    
    result = benchmark(custom_operation)
    
    # Custom assertions
    assert result.returncode == 0
    assert benchmark.stats.mean < your_threshold
```

### Test Data Generators

Create custom test data generators:

```python
def generate_custom_test_data(size: int, complexity: str) -> Path:
    """Generate custom test data for specific scenarios."""
    # Implementation here
    pass
```

## Reporting

### Report Contents

Performance reports include:

- **System Information**: Platform, CPU, memory details
- **Test Results**: Success/failure status and timing
- **Performance Metrics**: Detailed timing and resource usage
- **Issue Analysis**: Automatic detection of problems
- **Trends**: Comparison with previous runs (if available)

### Report Formats

- **JSON**: Machine-readable detailed report
- **Console**: Human-readable summary
- **Benchmark JSON**: pytest-benchmark statistical data

## Best Practices

### Test Development

1. **Isolation**: Each test should be independent
2. **Cleanup**: Always cleanup temporary resources
3. **Realistic Data**: Use representative test data
4. **Error Handling**: Tests should handle expected failures gracefully

### Performance Testing

1. **Warm-up**: Include warm-up runs to stabilize performance
2. **Multiple Iterations**: Run multiple iterations for statistical reliability
3. **System State**: Control system state during testing
4. **Baseline Establishment**: Establish performance baselines for comparison

### Maintenance

1. **Regular Updates**: Update performance targets as system evolves
2. **Test Data Refresh**: Periodically update test data to reflect real usage
3. **CI Integration**: Ensure tests run consistently in CI environment
4. **Documentation**: Keep this documentation updated with changes