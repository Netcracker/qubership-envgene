# Features Documentation

This directory contains documentation for EnvGene features.

## What is a Feature?

A feature is a distinct functional capability of EnvGene that:

- Represents a complete, self-contained functionality that can be understood independently
- Solves a specific problem or provides a specific capability
- May interact with other features but maintains clear functional boundaries

Each feature document describes a distinct functional capability of EnvGene, including its purpose, implementation approach, configuration, and usage.

Feature documentation describes what and how:

- What the feature does and why it exists
- How the feature works (implementation approach, configuration, usage)
- Conceptual understanding, technical specifications, and reference information

For step-by-step execution scenarios, see corresponding use cases in `/docs/use-cases/`. Each feature may have corresponding use cases in `/docs/use-cases/<feature-name>.md`.

## Feature Documentation Principles

### Feature Scope

- A feature represents a distinct functional area of EnvGene
- Features should be independent and understandable on their own
- Features can reference other features but should not duplicate their content

### Feature File Naming

- Use kebab-case: `feature-name.md`
- Be descriptive and match the feature's primary purpose
- Examples:
  - `blue-green-deployment.md` - Blue-Green deployment support
  - `environment-instance-generation.md` - Environment Instance generation process
  - `calculator-cli.md` - Effective Set Calculator CLI
