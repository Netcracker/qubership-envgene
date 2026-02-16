# Testing Approach

- [Testing Approach](#testing-approach)
  - [Terms](#terms)
  - [Testing Policy](#testing-policy)
  - [Test Types](#test-types)
    - [Smoke Testing](#smoke-testing)
  - [Test Cases](#test-cases)
    - [Creation Guidelines](#creation-guidelines)
    - [Test Case Template](#test-case-template)
    - [Template Description](#template-description)

## Terms

**User**: Human or system interacting with the solution

**Feature**: Discrete business function delivering value

**Use Case**: Scenario delivering user outcome. Sequence of interactions between a user and a system to achieve a specific goal

## Testing Policy

1. New functionality should not be released without:
   - Implementation of corresponding test cases
   - Successful execution of these tests
2. Each bug must undergo root cause analysis to determine:
   - Why existing test cases didn't catch it
   - If test coverage is possible, the bugfix should include new tests before release
3. All tests must be automated. During automation, each test must first be executed manually

## Test Types

### Smoke Testing

- **Execution Time**: Complete suite must run in ≤10 minutes
- **Triggers**:
  - Every Git commit/merge
  - Build/release workflows
- **Failure Handling**:
  - Doesn't block commits
  - Blocks build/release pipelines
- **Framework**: pytest

**Smoke Tests Testing Approach:**

- **Scope:** Tests target individual functions in isolation
- **Process:** For each function under test:
  1. Execute the function with predefined test data
  2. Validate outputs against reference data (file-by-file, character-by-character)
- **Failure Handling:** On mismatch, logs provide:
  - Test cases implemented in the failed data file.
  - Exact discrepancies detected (diff-style reporting)

**Note:**
Test case listing in failure logs indicates data mapping, not necessarily all cases failed

## Test Cases

### Creation Guidelines

- Test cases should be created from user perspective and essentially represent use cases
- Test cases should be created per use case
- Test cases should be grouped by features
- Test cases may include test data elements when it helps better/simpler representation of functionality
- Test cases should be test-type agnostic in their high-level description, allowing the same logical case to be applicable (though implemented differently) for various test types (e.g., smoke and end-to-end testing)
- Test cases should cover both sunny and rainy day scenarios

Test case creation should follow pragmatic principles, focusing on validating real user scenarios. While aiming for comprehensive coverage, recognize that test case development, implementation, and execution consume resources.

### Test Case Template

```markdown
## TC-XXX-XXX: [Brief Test Case Name]

**Status:** [New/Active/Archived]

**Description:**

**Test Data:**
- [Path/to/test/data/file1]
- [Path/to/test/data/file2]

**Pre-requisites:**
1. [Condition that must be true before test]
2. [Dependency]
3. [System state required for test]

**Steps**:
- [Action 1 with parameters]
- [Action 2 with parameters]

**Expected Results**:
- [System response]
- [State change]
- [Output validation]
```

### Template Description

**Test Case ID (TC-XXX-XXX)**:

Follows pattern TC-[Feature-ID]-[SEQ]

**Status**:

New: Case created but not automated
Active: In suite
Archived: Historical reference only

**Description:**

Brief title summarizing test scenario

**Test Data:**

Paths to test data files used in test case implementation. Used by automation to map reference files to test cases.

**Pre-requisites:**

System conditions required before execution. Configuration requirements. Dependencies that must be in place

**Steps:**

Actions required from the user to utilize the functionality, for example:

- Pipeline launch parameters (optionally with values)
- Commit events
- Other triggers

**Expected Results:**

Expected outcome. Expected system behavior. State change
