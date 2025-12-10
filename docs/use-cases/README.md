# Use Cases Documentation

This directory contains use cases for EnvGene features.

## What is a Use Case?

A use case is a step-by-step scenario that describes:

- When a feature is used (prerequisites and triggers)
- How to execute it (steps)
- What to expect (expected results)

Use cases complement feature documentation by providing practical, executable scenarios. For information about what features are and how they are organized, see [Features Documentation](/docs/features/README.md).

## When to Create Use Cases

Use cases should be created when they provide value beyond what's already documented in feature documentation.

**Create use cases when:**

- **Complex logic**: Multiple conditions, branching, or non-obvious sequence of steps
- **Critical for understanding**: High risk of misunderstanding
- **Different prerequisites/triggers/results**: Different input conditions, ways to trigger, or expected outcomes
- **Feature documentation doesn't cover scenarios**: Describes "what" but not "when/how" with different scenarios

**Don't create use cases when:**

- **No variability**: Single algorithm, single execution path, always same result
- **Simple deterministic logic**: Straightforward algorithm without branching, easily understood from feature documentation
- **Fully documented in feature docs**: Algorithm described with examples, all steps clear, no ambiguities

**Rule of thumb**: Use cases describe *scenarios* (different ways things can happen), not just *algorithms* (how things work). If feature documentation already describes the algorithm with examples and there's no variability in execution paths or outcomes, a use case may be redundant.

## Use Case Organization

Use cases are organized in a two-level hierarchy:

### Feature (Use Case Files)

Each feature has its own use case file in the `use-cases` directory. The use case file corresponds to a feature documented in `/docs/features/`.

**Use Case File Naming:**

- Use kebab-case: `feature-name.md`
- Match the corresponding feature documentation name in `/docs/features/`

### Group (Sections within Use Case Files)

Within each use case file, use cases **may be** grouped into logical groups that represent sub-functions or related scenarios.

**Group Formation Principles:**

- Groups represent distinct aspects or sub-functions within the main feature
- Groups are based on functional boundaries
- Groups may represent independent sub-functions that can be understood and tested separately

**Group Structure:**

- Each group is a section with a level 2 heading (`## Group Name`)
- Right after the group heading, include a description explaining what the group covers (its purpose)
- Use cases within a group are defined as level 3 headings following the naming convention: `### UC-<PREFIX>-<GROUP>-<NUMBER>: <Title>`

## Feature Use Cases Template

Each use case file should follow this template:

1. **Overview**:
   - Brief description of what the use case file covers
   - Reference to the corresponding [feature documentation](/docs/features/)
   - Diagram showing execution order of sub-functions (include when there are multiple groups and their execution order needs to be explicitly shown)
2. **Groups**: Each group with its description (see [Group Structure](#group-sections-within-use-case-files))
3. [**Use Cases**](#use-case-template): Individual use cases following the use case template (see below)

See [Environment Instance Generation Use Cases](/docs/use-cases/environment-instance-generation.md) and [Blue-Green Deployment Use Cases](/docs/use-cases/blue-green-deployment.md) for examples.

## Use Case Template

When creating a new use case, follow this template:

```markdown
### UC-<PREFIX>-<GROUP>-<NUMBER>: Use Case Title

**Pre-requisites:**

1. First prerequisite condition
2. Second prerequisite condition with example configuration (if applicable):

    ```yaml
    # Example configuration or template
    key: value
    ```

3. Additional prerequisites as needed

**Trigger:**

When parameters are identical for both pipelines:

Instance pipeline (GitLab or GitHub) is started with parameters:
1. `<PARAMETER_1>: <value>`
2. `<PARAMETER_2>: <value>`

When parameters differ between pipelines:

1. GitLab Instance pipeline is started with parameters:
   1. `<PARAMETER_1>: <value>`
   2. `<PARAMETER_2>: <value>`
2. GitHub Instance pipeline is started with parameters:
   1. `<PARAMETER_1>: <value>`
   2. `<PARAMETER_2>: <value>`

**Steps:**

1. The `<job_name>` job runs in the pipeline:
   1. First step description
   2. Second step description
   3. Additional steps as needed

**Results:**

1. First expected result
2. Second expected result with specific path or state:
   - File path: `/path/to/resource`
   - Object state: `key: value`
3. Additional results as needed
```

### Use Case Sections

- **Pre-requisites**:
  - List all conditions that must be met before the use case can be executed
  - May include state of Environment Inventory, Environment Instance, or other required objects
  - Include all prerequisites necessary for understanding and executing the use case; omit only trivial prerequisites that are obvious and don't contribute to understanding

- **Trigger**:
  - Both GitLab and GitHub pipelines must be described
  - When parameters are identical for both pipelines, list them once with a note: "Instance pipeline (GitLab or GitHub) is started with parameters:"
  - When parameters differ between pipelines, list them separately for each pipeline
  - When multiple trigger conditions are possible (e.g., "one of the following"), use a Note block to indicate this
  - Use placeholders (`<placeholder>`) for variable values, but specify actual values when they are important for understanding the use case

- **Steps**:
  - Number each step sequentially
  - Use nested numbering for sub-steps within a job execution
  - Describe what EnvGene does, not what the user does
  - Be specific about which job performs the operation
  - Include all steps necessary for understanding and executing the use case; omit only trivial steps that are obvious and don't contribute to understanding

- **Results**:
  - List all expected outcomes
  - Be specific about what should be created, updated, or changed
  - Include file paths or object states when relevant
  - Use bullet points or sub-items to break down complex results

## Use Case Naming and Numbering Convention

### Format

Use format: `UC-<PREFIX>-<GROUP>-<NUMBER>: <Descriptive Title>`

- **Prefix**: Short abbreviation identifying the feature area
  - Examples: `EIG` (Environment Instance Generation), `BG` (Blue-Green), `ES` (Effective Set)
  - Should be 2-4 uppercase letters
  - Should match the feature filename or its abbreviation

- **Group** (optional): Short abbreviation identifying the group within the feature
  - Examples: `NF` (Namespace Folder), `TA` (Template Artifacts)
  - Should be 2-3 uppercase letters
  - Required when use cases are organized into groups to ensure unique IDs across the feature
  - Omit if use cases are not grouped

- **Number**: Sequential number within the group (or feature if no groups)
  - Use integers starting from 1: `1`, `2`, `3`, etc.
  - For inserting use cases between existing ones, use decimal notation: `2.1`, `2.2`, `3.1`, etc.
  - Decimal numbers allow insertion without renumbering existing cases

- **Title**: Concise, descriptive title
  - Should clearly indicate what the use case demonstrates
  - Use title case

### Numbering Rules

1. **Unique IDs**: Each use case ID must be unique within the use case file

2. **Group-based Numbering**: When use cases are organized into groups:
   - Each group has its own sequential numbering starting from 1
   - Use group prefix in the ID to ensure uniqueness: `UC-XXX-GROUP-1`, `UC-XXX-GROUP-2`, etc.
   - Example: `UC-EIG-NF-1`, `UC-EIG-NF-2` (Namespace Folder group) and `UC-EIG-TA-1`, `UC-EIG-TA-2` (Template Artifacts group)

3. **Non-grouped Numbering**: When use cases are not organized into groups:
   - Use sequential numbering across the entire feature: `UC-XXX-1`, `UC-XXX-2`, `UC-XXX-3`
   - No group prefix needed

4. **Inserting New Use Cases**: Use decimal notation to insert between existing cases:
   - To insert between `UC-XXX-GROUP-2` and `UC-XXX-GROUP-3`: use `UC-XXX-GROUP-2.1`, `UC-XXX-GROUP-2.2`, etc.
   - To insert between `UC-XXX-5` and `UC-XXX-6`: use `UC-XXX-5.1`, `UC-XXX-5.2`, etc.

5. **Examples**:

   ```text
   # With groups:
   UC-EIG-NF-1: Namespace NOT in BG Domain with deploy_postfix
   UC-EIG-NF-2: Namespace NOT in BG Domain without deploy_postfix
   UC-EIG-TA-1: Environment Instance Generation with Common Artifact Only
   UC-EIG-TA-2: Environment Instance Generation with Blue-Green Artifacts
   
   # Without groups:
   UC-BG-1: Blue-Green Warmup Operation
   UC-BG-2: Blue-Green Switch Operation
   ```
