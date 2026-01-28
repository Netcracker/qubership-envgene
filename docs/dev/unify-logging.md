# Unified Logging – Demo Overview

This document describes the logging improvements in issue: https://github.com/Netcracker/qubership-envgene/issues/751

## Motivation

Previously:
- Logging logic was duplicated across files
- Log formatting and levels were inconsistent
- Log level configuration was limited
- Different colours for the same Log level across jobs
- No log level control on Instance Project

Now:
- Logging is centralized
- Log levels are configurable
- Output is more readable and consistent
- Colour is consistent across jobs
- Log level can be set on Instance Project
---

## Key Changes

### 1. Centralized Logging

A single logging module was introduced.
All other modules import and use it.

**Benefits:**
- No duplicated logging logic
- Easier maintenance
- Consistent format across the repository

---

### 2. Coloured Log Levels

Different log levels now have consistent colours across jobs:

| Level  | Colour   |
|------|--------|
| DEBUG | Blue   |
| INFO (default) | White  |
| WARNING | Yellow |
| ERROR | Red    |

---

### 3. New Logging Parameter

A new parameter was added to control logging behavior.

https://github.com/Netcracker/qubership-envgene/blob/a823f450a671d058813991b218b9afde59f6db41/docs/envgene-repository-variables.md#envgene_log_level

---

### 4. Parameter Logging Script for Generated Jobs

A script was added that:
- Runs at the start of every generated job
- Logs input parameters

---