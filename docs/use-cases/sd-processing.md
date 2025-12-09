# SD Processing Use Cases

- [SD Processing Use Cases](#sd-processing-use-cases)
  - [SD Processing Details](#sd-processing-details)
  - [Use Cases](#use-cases)

## SD Processing Details

For information on SD processing, refer to the [feature documentation](/docs/features/sd-processing.md).

## Use Cases

| Use Case | SD_SOURCE_TYPE | SD_VERSION / SD_DATA    | SD_REPO_MERGE_MODE / SD_DELTA         | Prerequisites                                                    | Result                                                                                                                      |
|:--------:|:--------------:|:-----------------------:|:-------------------------------------:|:-----------------------------------------------------------------|:----------------------------------------------------------------------------------------------------------------------------|
| UC-1-1   | `artifact`     | single SD_VERSION       | `replace`                             | AppDef and RegDef must exist for each app:ver in SD_VERSION      | Full SD replaced with SD from artifact                                                                                      |
| UC-1-2   | `artifact`     | single SD_VERSION       | `extended-merge`                      | AppDef and RegDef must exist for each app:ver in SD_VERSION      | SD merged with repository Full SD (extended-merge), result saved as Full SD                                                 |
| UC-1-3   | `artifact`     | single SD_VERSION       | `basic-merge` (default)               | AppDef and RegDef must exist for each app:ver in SD_VERSION      | SD merged with repository Full SD (basic-merge), result saved as Full SD                                                    |
| UC-1-4   | `artifact`     | single SD_VERSION       | `basic-exclusion-merge`               | AppDef and RegDef must exist for each app:ver in SD_VERSION      | SD merged with repository Full SD (basic-exclusion-merge), result saved as Full SD                                          |
| UC-1-5   | `artifact`     | multiple SD_VERSION     | `basic-merge` (default)               | AppDef and RegDef must exist for each app:ver in SD_VERSION      | All SDs from SD_VERSION are basic-merged, then merged with repository Full SD using basic-merge, saved as Full SD           |
| UC-1-6   | `artifact`     | multiple SD_VERSION     | `basic-exclusion-merge`               | AppDef and RegDef must exist for each app:ver in SD_VERSION      | All SDs from SD_VERSION are basic-merged, then merged with repository Full SD using basic-exclusion-merge, saved as Full SD |
| UC-1-7   | `artifact`     | multiple SD_VERSION     | `extended-merge`                      | AppDef and RegDef must exist for each app:ver in SD_VERSION      | All SDs from SD_VERSION are basic-merged, then merged with repository Full SD using extended-merge, saved as Full SD        |
| UC-1-8   | `artifact`     | multiple SD_VERSION     | `replace`                             | AppDef and RegDef must exist for each app:ver in SD_VERSION      | All SDs from SD_VERSION are basic-merged, then Full SD replaced with merge result                                           |
| UC-1-9   | `artifact`     | single SD_VERSION       | SD_DELTA=true (deprecated)            | AppDef and RegDef must exist for each app:ver in SD_VERSION      | Same as for UC-1-2                                                                                                          |
| UC-1-10  | `artifact`     | single SD_VERSION       | SD_DELTA=false (deprecated)           | AppDef and RegDef must exist for each app:ver in SD_VERSION      | Same as for UC-1-1                                                                                                          |
| UC-2-1   | `json`         | single SD_DATA          | `replace`                             | None                                                             | Full SD replaced with SD from JSON                                                                                          |
| UC-2-2   | `json`         | single SD_DATA          | `extended-merge`                      | None                                                             | SD merged with repository Full SD (extended-merge), result saved as Full SD                                                 |
| UC-2-3   | `json`         | single SD_DATA          | `basic-merge` (default)               | None                                                             | SD merged with repository Full SD (basic-merge), result saved as Full SD                                                    |
| UC-2-4   | `json`         | single SD_DATA          | `basic-exclusion-merge`               | None                                                             | SD merged with repository Full SD (basic-exclusion-merge), result saved as Full SD                                          |
| UC-2-5   | `json`         | multiple SD_DATA        | `basic-merge` (default)               | None                                                             | All SDs from SD_DATA are basic-merged, then merged with repository Full SD using basic-merge, saved as Full SD              |
| UC-2-6   | `json`         | multiple SD_DATA        | `basic-exclusion-merge`               | None                                                             | All SDs from SD_DATA are basic-merged, then merged with repository Full SD using basic-exclusion-merge, saved as Full SD    |
| UC-2-7   | `json`         | multiple SD_DATA        | `extended-merge`                      | None                                                             | All SDs from SD_DATA are basic-merged, then merged with repository Full SD using extended-merge, saved as Full SD           |
| UC-2-8   | `json`         | multiple SD_DATA        | `replace`                             | None                                                             | All SDs from SD_DATA are basic-merged, then Full SD replaced with merge result                                              |
| UC-2-9   | `json`         | single SD_DATA          | SD_DELTA=true (deprecated)            | None                                                             | Same as for UC-2-2                                                                                                          |
| UC-2-10  | `json`         | single SD_DATA          | SD_DELTA=false (deprecated)           | None                                                             | Same as for UC-2-1                                                                                                          |
