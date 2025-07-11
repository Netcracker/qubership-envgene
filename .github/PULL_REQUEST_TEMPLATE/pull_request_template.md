# Pull Request

## Description
<!-- Provide a brief description of the changes in this PR -->

## Related Issues
<!-- Link to any related issues using the format: Closes #123, Fixes #456 -->

## Type of Change
<!-- Mark the appropriate option with an [x] -->
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Refactoring (no functional changes)
- [ ] Performance improvement
- [ ] Test addition or update

## Checklist
<!-- Mark completed items with an [x] -->

### General
- [ ] My code follows the style guidelines of this project
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes

### Error Handling
- [ ] Custom error classes from `envgenehelper.errors` are used for all error cases
- [ ] All error messages include error codes following the ENVGENE-XXXX format
- [ ] Error messages are user-friendly and provide clear guidance on how to resolve the issue
- [ ] No sensitive information is exposed in error messages
- [ ] Errors are propagated to pipeline output and not swallowed by handlers

### Error Documentation
- [ ] All new error codes are documented in error-catalog.md
- [ ] Documentation includes all required sections (ID, Component, When, What, Error, Resolution)
- [ ] Error code ranges are used appropriately (business: 0001-1499, validation: 4000-6999, etc.)

### Error Testing
- [ ] Tests are included for error scenarios
- [ ] Error messages are verified to be displayed correctly in the pipeline output

## Screenshots
<!-- If applicable, add screenshots to help explain your changes -->

## Additional Notes
<!-- Add any other information about the PR here -->
