# Calculator CLI Use Cases

- [Calculator CLI Use Cases](#calculator-cli-use-cases)
  - [Overview](#overview)
  - [deployPostfix Matching Logic](#deploypostfix-matching-logic)
    - [UC-CC-DP-1: Exact Match](#uc-cc-dp-1-exact-match)
    - [UC-CC-DP-2: BG Domain Match](#uc-cc-dp-2-bg-domain-match)
    - [UC-CC-DP-3: No Exact Match Found](#uc-cc-dp-3-no-exact-match-found)
    - [UC-CC-DP-4: No BG Domain Match Found](#uc-cc-dp-4-no-bg-domain-match-found)

## Overview

This document covers use cases for [Calculator CLI](/docs/features/calculator-cli.md) operations related to Effective Set v2.0 generation, specifically focusing on `deployPostfix` matching logic for Blue-Green Deployment support.

> [!NOTE]
> These use cases apply only to Effective Set v2.0. Use cases for Effective Set v1.0 are not planned.

## deployPostfix Matching Logic

This section covers use cases for [deployPostfix Matching Logic](/docs/features/calculator-cli.md#version-20-deploypostfix-matching-logic). The matching logic matches `deployPostfix` values from Solution Descriptor(SD) to Namespace folders in Environment Instance.

### UC-CC-DP-1: Exact Match

**Pre-requisites:**

1. Environment Instance exists with:
   1. Namespace objects
   2. A Namespace folder whose name exactly matches the `deployPostfix` value from Solution Descriptor
2. SD exists with `deployPostfix` values in application elements

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job runs in the pipeline:
   1. Reads SD and extracts `deployPostfix` values from application elements
   2. For each `deployPostfix` value from SD:
      1. Attempts exact match: searches for a Namespace folder in Environment Instance whose name exactly matches the `deployPostfix` value
      2. Finds exact match
      3. Uses that Namespace folder

**Results:**

1. `deployPostfix` value from SD is matched to the Namespace folder with exact name match
2. Applications from SD are associated with the matching Namespace folder in Effective Set

### UC-CC-DP-2: BG Domain Match

**Pre-requisites:**

1. Environment Instance exists with:
   1. Namespace objects
   2. BG Domain object exists with `origin` and `peer` namespaces with corresponding folders in Environment Instance that match `deployPostfix` values:
      1. `origin` Namespace (from BG Domain object) folder name equals `deployPostfix` + `-origin` (e.g., `bss-origin`)
      2. `peer` Namespace (from BG Domain object) folder name equals `deployPostfix` + `-peer` (e.g., `bss-peer`)
2. SD exists with `deployPostfix` values in application elements:
   1. A `deployPostfix` value that matches `origin` Namespace folder (e.g., `deployPostfix: "bss"` matches `bss-origin`)
   2. A `deployPostfix` value that matches `peer` Namespace folder (e.g., `deployPostfix: "bss"` matches `bss-peer`)

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job runs in the pipeline:
   1. Reads SD and extracts `deployPostfix` values from application elements
   2. For each `deployPostfix` value from SD:
      1. Attempts exact match: searches for a Namespace folder in Environment Instance whose name exactly matches the `deployPostfix` value
      2. No exact match is found
      3. Searches for a Namespace folder in BG Domain:
         1. Searches for a Namespace folder with role `origin` (from BG Domain object) whose name equals `deployPostfix` + `-origin`
         2. Searches for a Namespace folder with role `peer` (from BG Domain object) whose name equals `deployPostfix` + `-peer`
      4. Finds matching Namespace folder (either `origin` or `peer`)
      5. Uses that Namespace folder

**Results:**

1. `deployPostfix` value from SD is matched to either the `origin` or `peer` Namespace folder in BG Domain (with `-origin` or `-peer` suffix, depending on which match is found)
2. Applications from SD are associated with the matching Namespace folder (`origin` or `peer`) in Effective Set

### UC-CC-DP-3: No Exact Match Found

**Pre-requisites:**

1. Environment Instance exists with:
   1. Namespace objects
   2. No Namespace folder whose name exactly matches the `deployPostfix` value from SD
2. SD exists with `deployPostfix` values in application elements

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job runs in the pipeline:
   1. Reads SD and extracts `deployPostfix` values from application elements
   2. For each `deployPostfix` value from SD:
      1. Attempts exact match: searches for a Namespace folder whose name exactly matches the `deployPostfix` value
      2. No exact match is found
      3. No matching Namespace folder is found for the `deployPostfix` value
   3. Effective Set generation fails with an error

**Results:**

1. No Namespace folder is matched to the `deployPostfix` value from SD
2. Applications from SD with this `deployPostfix` value are not associated with any Namespace folder in Effective Set
3. Effective Set generation fails with an error indicating that no matching Namespace folder was found in Environment Instance for the `deployPostfix` value from SD (e.g., `Error: Cannot find Namespace folder in Environment Instance for deployPostfix: "<deployPostfix>"`)

### UC-CC-DP-4: No BG Domain Match Found

**Pre-requisites:**

1. Environment Instance exists with:
   1. Namespace objects
   2. No Namespace folder whose name exactly matches the `deployPostfix` value from SD
   3. BG Domain object exists with `origin` and `peer` namespaces and corresponding folders in Environment Instance, but no matching BG Domain namespace folder exists for the `deployPostfix` value from SD:
      - `deployPostfix` + `-origin` does not match the `origin` Namespace folder name, **OR**
      - `deployPostfix` + `-peer` does not match the `peer` Namespace folder name, **OR**
      - Both do not match
2. SD exists with `deployPostfix` values in application elements

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job runs in the pipeline:
   1. Reads SD and extracts `deployPostfix` values from application elements
   2. For each `deployPostfix` value from SD:
      1. Attempts exact match: searches for a Namespace folder whose name exactly matches the `deployPostfix` value
      2. No exact match is found
      3. Searches for a Namespace folder in BG Domain:
         1. Searches for a Namespace folder with role `origin` (from BG Domain object) whose name equals `deployPostfix` + `-origin`
         2. Searches for a Namespace folder with role `peer` (from BG Domain object) whose name equals `deployPostfix` + `-peer`
      4. No matching BG Domain namespace folder is found
   3. No matching Namespace folder is found for the `deployPostfix` value
   4. Effective Set generation fails with an error

**Results:**

1. No Namespace folder is matched to the `deployPostfix` value from SD
2. Applications from SD with this `deployPostfix` value are not associated with any Namespace folder in Effective Set
3. Effective Set generation fails with an error indicating that no matching Namespace folder was found in Environment Instance for the `deployPostfix` value(s) from SD. The error message lists all `deployPostfix` values that could not be matched (e.g., `Cannot find Namespace folder in Environment Instance for deployPostfix: "<deployPostfix>", "<deployPostfix>"`)
