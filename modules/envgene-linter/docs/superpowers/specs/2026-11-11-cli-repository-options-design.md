# Explicit repository paths in the CLI

- [Purpose and approach](#purpose-and-approach)
- [Command contract](#command-contract)
- [Recommendation contract](#recommendation-contract)
- [Validation](#validation)

## Purpose and approach

Supply instance and template paths together when reviewing ParameterSet changes across two repositories.
The requested interface adds short options to the existing Click command and reuses PLACE-12 template inspection.
This is a small extension to repository selection, with no new dependencies or automatic migration.

The chosen approach preserves the positional repository argument and the existing `--template-repo` option.
Replacing the positional argument would break existing commands. A separate migration command would exceed this request.
Implementation choices here preserve existing command behavior unless an explicit option selects another directory.

## Command contract

```bash
envgene-linter check -i /path/to/instance-repository -t /path/to/template-repository
```

- `-i PATH` and `--instance-repo PATH` select the checked repository.
- `-t PATH` and `--template-repo PATH` supply optional local template context for PLACE-12.
- `REPO` remains an optional positional argument, including for template-only checks.
- If neither `REPO` nor `-i` is supplied, check the current directory.
- Reject simultaneous `REPO` and `-i`, even when their paths are equal, before writing reports or `.gitignore`.
- Validate both option paths as existing directories. Accept relative paths and paths containing spaces or Unicode.
- Continue accepting either the template repository root or its `templates/` directory as template context.
- Preserve source inspection limits and symbolic-link safeguards.

Both reports and report ignore entries belong to the checked repository.
The template source supplies context for PLACE-12 and does not receive a separate lint run or report.
Neither option automatically edits ParameterSets, descriptors, or Environment Inventory bindings.

## Recommendation contract

When local template context is supplied, prepend the absolute instance and template repository roots to each
PLACE-12 recommendation. Existing `environments/` source paths belong to the instance root.
Existing `templates/` destination and descriptor paths belong to the template root.
An input pointing to `templates/` identifies its parent as the template repository root.

Apply the same context to complete relocation candidates, partial shared-value proposals, and unresolved destinations.
Keep the engine recommendation identical in HTML, JSON, and console output.
Preserve JSON's six fields and omit `type`. Do not change grouping, eligibility, bindings, or relocation decisions.

## Validation

Exercise real Click invocations for short and long options, defaults, legacy positional commands, conflicting inputs,
and invalid directories. Verify output locations and absence of output changes for rejected commands.
Check complete and partial PLACE-12 recommendations, template-directory inputs, identical HTML/JSON guidance,
and unchanged configuration sources. Run the complete module suite and the applicable code and documentation linters.
