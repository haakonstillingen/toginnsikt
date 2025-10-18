# Test-Driven Development (TDD) Guidelines for Cursor Agents

## Overview

This document establishes Test-Driven Development (TDD) principles and guidelines for all Cursor agents working on the Toginnsikt project. TDD ensures high code quality, reduces bugs, and makes refactoring safe and confident.

## Core TDD Principles

### 1. Red-Green-Refactor Cycle

**RED** → **GREEN** → **REFACTOR** → Repeat

1. **RED**: Write a failing test that describes the desired behavior
2. **GREEN**: Write the minimum code to make the test pass
3. **REFACTOR**: Improve the code while keeping tests green
4. **Repeat**: Continue the cycle for each new feature

### 2. Test-First Development

- **Always write tests before implementation**
- Tests serve as executable documentation
- Tests define the contract and expected behavior
- Tests catch regressions immediately

### 3. The Three Laws of TDD

1. **First Law**: You may not write production code until you have written a failing unit test
2. **Second Law**: You may not write more of a unit test than is sufficient to fail
3. **Third Law**: You may not write more production code than is sufficient to pass the currently failing test

## TDD Workflow for Cursor Agents

### Phase 1: Analysis and Planning
1. **Understand the requirement** - What exactly needs to be built?
2. **Identify test scenarios** - What should the code do? What edge cases exist?
3. **Plan test structure** - Unit tests, integration tests, E2E tests
4. **Create test file** - Set up the test framework and basic structure

### Phase 2: Red Phase (Write Failing Tests)
1. **Write the test first** - Describe the expected behavior
2. **Run the test** - Verify it fails (RED)
3. **Document the failure** - Understand why it fails
4. **Repeat** - Write more tests for different scenarios

### Phase 3: Green Phase (Make Tests Pass)
1. **Write minimal code** - Just enough to make tests pass
2. **Run tests frequently** - After each small change
3. **Keep it simple** - Don't over-engineer yet
4. **Verify all tests pass** - Ensure no regressions

### Phase 4: Refactor Phase (Improve Code)
1. **Improve code quality** - Better naming, structure, performance
2. **Keep tests green** - All tests must still pass
3. **Remove duplication** - DRY principle
4. **Optimize** - Performance improvements

## Test Categories and Structure

### 1. Unit Tests (`test_*.py`)
**Purpose**: Test individual functions/methods in isolation
**Scope**: Single function, class, or method
**Dependencies**: Mocked external dependencies
**Speed**: Fast (< 1 second per test)
**Examples**:
```python
def test_matches_final_destination_basic_patterns(self):
    """Test basic pattern matching functionality"""
    self.assertTrue(self.collector.matches_final_destination("Lysaker", "Lysaker"))
    self.assertFalse(self.collector.matches_final_destination("Ski", "Lysaker"))
```

### 2. Integration Tests (`test_*_integration.py`)
**Purpose**: Test interaction between components
**Scope**: Multiple components working together
**Dependencies**: Real database, APIs (when available)
**Speed**: Medium (1-10 seconds per test)
**Examples**:
```python
def test_route_loading_with_real_database(self):
    """Test route loading with real database (if available)"""
    routes = self.collector.load_commute_routes()
    self.assertGreaterEqual(len(routes), 0)
```

### 3. End-to-End Tests (`test_*_e2e.py`)
**Purpose**: Test complete user workflows
**Scope**: Full application pipeline
**Dependencies**: Complete system setup
**Speed**: Slow (10+ seconds per test)
**Examples**:
```python
def test_e2e_valid_routes_collection(self):
    """Test end-to-end collection with valid routes"""
    routes = self.collector.load_commute_routes()
    departures = self.collector.fetch_planned_departures(route, start_time)
    self.assertEqual(len(departures), expected_count)
```

## Test Naming Conventions

### Test Method Names
Use descriptive names that explain the scenario:
```python
def test_matches_final_destination_with_pipe_separated_patterns(self):
def test_route_validation_skips_empty_patterns(self):
def test_duplicate_route_detection_works_correctly(self):
def test_e2e_collection_with_mixed_valid_invalid_routes(self):
```

### Test Class Names
Use descriptive class names that indicate the component being tested:
```python
class TestRouteValidation(unittest.TestCase):
class TestRouteValidationIntegration(unittest.TestCase):
class TestRouteValidationE2E(unittest.TestCase):
```

### Test File Names
Use consistent naming patterns:
- `test_<component>.py` - Unit tests
- `test_<component>_integration.py` - Integration tests
- `test_<component>_e2e.py` - End-to-end tests

## Test Structure and Organization

### 1. Test Class Structure
```python
class TestComponentName(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method"""
        # Initialize test data, mocks, etc.
    
    def tearDown(self):
        """Clean up after each test method"""
        # Clean up resources
    
    def test_specific_behavior(self):
        """Test specific behavior with descriptive name"""
        # Arrange - Set up test data
        # Act - Execute the code under test
        # Assert - Verify the results
```

### 2. Test Method Structure (AAA Pattern)
```python
def test_example_behavior(self):
    """Test description explaining what this test verifies"""
    # ARRANGE - Set up test data and conditions
    input_data = "test input"
    expected_result = "expected output"
    
    # ACT - Execute the code under test
    actual_result = function_under_test(input_data)
    
    # ASSERT - Verify the results
    self.assertEqual(actual_result, expected_result)
```

## Mocking and Test Doubles

### When to Use Mocks
- **External APIs** - Don't make real API calls in unit tests
- **Database connections** - Use in-memory or mock databases
- **File system** - Mock file operations
- **Time-dependent code** - Mock datetime.now()
- **Random values** - Mock random number generation

### Mock Examples
```python
# Mock database connection
mock_conn = Mock()
mock_cursor = Mock()
mock_conn.cursor.return_value = mock_cursor
self.collector.get_db_connection = Mock(return_value=mock_conn)

# Mock API response
mock_api_response = {'data': {'stopPlace': {'estimatedCalls': []}}}
with patch.object(self.collector, 'make_api_request', return_value=mock_api_response):
    result = self.collector.fetch_planned_departures(route, start_time)
```

## Error Handling and Edge Cases

### Test Error Scenarios
```python
def test_handles_invalid_input_gracefully(self):
    """Test that function handles invalid input without crashing"""
    with self.assertRaises(ValueError):
        function_under_test(None)
    
def test_handles_empty_data_correctly(self):
    """Test behavior with empty input data"""
    result = function_under_test([])
    self.assertEqual(result, [])

def test_handles_network_failure(self):
    """Test behavior when external service fails"""
    with patch.object(self.collector, 'make_api_request', side_effect=Exception("Network error")):
        result = self.collector.fetch_data()
        self.assertEqual(result, [])
```

### Edge Cases to Consider
- **Empty inputs** - Empty strings, lists, dictionaries
- **Null/None values** - Handle gracefully
- **Boundary values** - Min/max values, edge of ranges
- **Invalid data types** - Wrong types passed to functions
- **Network failures** - API timeouts, connection errors
- **Database errors** - Connection lost, query failures
- **Concurrent access** - Race conditions, threading issues

## Test Data Management

### Test Data Principles
1. **Isolated** - Each test should be independent
2. **Minimal** - Use only necessary data
3. **Realistic** - Use real-world data patterns
4. **Maintainable** - Easy to update and understand

### Test Data Organization
```
testdata/
├── api_responses/
│   ├── valid_departure_response.json
│   └── empty_response.json
├── database/
│   ├── test_routes.sql
│   └── test_departures.sql
└── fixtures/
    ├── sample_routes.json
    └── expected_outputs.json
```

## Continuous Integration and Testing

### Pre-commit Testing
```bash
# Run all tests before committing
python run_route_validation_tests.py

# Run specific test categories
python run_route_validation_tests.py --unit-only
python run_route_validation_tests.py --integration-only
python run_route_validation_tests.py --e2e-only
```

### Test Coverage
- Aim for **90%+ code coverage** on critical paths
- Focus on **business logic** over framework code
- Test **error paths** and **edge cases**
- Use coverage tools: `coverage.py`, `pytest-cov`

## TDD Best Practices for Cursor Agents

### 1. Start Small
- Begin with the simplest test case
- Build complexity gradually
- One test at a time

### 2. Write Clear Tests
- Use descriptive names
- Add comments explaining complex scenarios
- Keep tests focused on one behavior

### 3. Test Behavior, Not Implementation
- Test what the code does, not how it does it
- Avoid testing private methods directly
- Focus on public interfaces

### 4. Keep Tests Fast
- Unit tests should run in milliseconds
- Use mocks for slow operations
- Separate slow tests from fast tests

### 5. Maintain Test Quality
- Refactor tests when refactoring production code
- Remove obsolete tests
- Keep tests up to date with requirements

## Common TDD Anti-patterns to Avoid

### ❌ Don't Do This
```python
# Testing implementation details
def test_uses_correct_algorithm(self):
    self.assertEqual(algorithm_type, "quicksort")

# Testing too much at once
def test_everything(self):
    # 50 lines of complex test logic
    pass

# Brittle tests
def test_specific_output_format(self):
    self.assertEqual(str(result), "exact string with spaces")
```

### ✅ Do This Instead
```python
# Testing behavior
def test_sorts_list_correctly(self):
    unsorted = [3, 1, 2]
    sorted_list = sort_function(unsorted)
    self.assertEqual(sorted_list, [1, 2, 3])

# Focused tests
def test_sorts_empty_list(self):
    result = sort_function([])
    self.assertEqual(result, [])

# Robust tests
def test_contains_expected_elements(self):
    result = process_data(input_data)
    self.assertIn("expected_element", result)
```

## Integration with Cursor Agents

### For AI Agents Working on This Project

1. **Always start with tests** when implementing new features
2. **Use the existing test structure** as a template
3. **Follow the naming conventions** established in this document
4. **Run tests frequently** during development
5. **Update tests** when requirements change
6. **Ask for test review** when submitting code

### Code Review Checklist for TDD
- [ ] Are there tests for the new functionality?
- [ ] Do tests cover both happy path and error cases?
- [ ] Are tests readable and well-named?
- [ ] Do tests run independently?
- [ ] Is test data realistic and minimal?
- [ ] Are mocks used appropriately?
- [ ] Do tests provide good error messages when they fail?

## Conclusion

TDD is not just about writing tests—it's about **designing better software** through the discipline of thinking about behavior before implementation. By following these guidelines, Cursor agents can contribute to a more robust, maintainable, and reliable codebase.

**Remember**: Good tests are a safety net that allows confident refactoring and feature development. They serve as living documentation and help prevent regressions. Invest in test quality, and the codebase will reward you with stability and maintainability.
