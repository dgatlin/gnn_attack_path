# Agentic System Tests

This directory contains comprehensive tests for the agentic aspects of the GNN Attack Path system.

## Test Files

- `test_agentic_simple.py` - Simplified test suite that works without external dependencies (17/17 tests passing)
- `test_agentic_system.py` - Full test suite with comprehensive mocking and error handling

## Running Tests

```bash
# Run simplified tests (recommended for CI/CD)
python tests/agentic/test_agentic_simple.py

# Run full test suite (requires proper mocking setup)
python -m pytest tests/agentic/test_agentic_system.py -v
```

## Test Coverage

- **Agent Component Tests**: Intent recognition, target extraction, algorithm selection
- **Remediation Tests**: Action generation, prioritization, simulation
- **API Integration Tests**: All REST endpoints and workflows
- **Error Handling Tests**: Graceful degradation and fallback behavior
- **Concurrent Request Tests**: System stability under load

## Dependencies

The simplified test suite requires no external dependencies and uses mock data for all external services.
