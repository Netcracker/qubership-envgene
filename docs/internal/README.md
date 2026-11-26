# EnvGene: internal documentation

For the team that builds EnvGene and for other Cloud Platform components. Customer-facing
documentation lives in [docs/public/](/docs/public/README.md).

## The documentation folders

| Folder | Readers | Holds |
| --- | --- | --- |
| [`docs/public/`](/docs/public/README.md) | users of EnvGene | tutorials, how-to guides, feature docs, use cases, parameter and object reference |
| `docs/internal/` | the team, other components | how this repository is built and released, design records, analyses, test cases |
| [`docs/data/`](/docs/data/README.md) | documentation authors | the original sources the documentation embeds |
| [`docs/glossary.md`](/docs/glossary.md) | everyone | the terms of the domain, one meaning each |

## Development guides

| Page | What it covers |
| --- | --- |
| [artifact-naming.md](/docs/dev/artifact-naming.md) | How build artifacts and images are named, and the branch-name sanitizing behind it |
| [creating-cr.md](/docs/dev/creating-cr.md) | The change request (CR): its body template, the six sections, and good and bad examples |
| [docker-build-workflow.md](/docs/dev/docker-build-workflow.md) | How the Docker images of this repository are built |
| [external-cred-provision-pypi-publish-workflow.md](/docs/dev/external-cred-provision-pypi-publish-workflow.md) | Publishing the `external-cred-provision` package |
| [global-pre-commit-hooks.md](/docs/dev/global-pre-commit-hooks.md) | The pre-commit hooks every clone must run, and how to install them |
| [new_debug_approach.md](/docs/dev/new_debug_approach.md) | Debugging a pipeline run |
| [sync-github-workflow.md](/docs/dev/sync-github-workflow.md) | The workflow that syncs the GitHub copy of this code |
| [sync-github-folder-workflow.md](/docs/dev/sync-github-folder-workflow.md) | The folder-scoped variant of the same sync |
| [unify-logging.md](/docs/dev/unify-logging.md) | One logging approach across the modules |
| [designs/](/docs/dev/designs/) | Design documents of the work in progress |

## Design records

| Folder | What it holds |
| --- | --- |
| [adr/](/docs/adr/) | Architecture decision records: the context, the options weighed, the decision and its consequences |
| [technical-design/](/docs/technical-design/) | The design of the instance pipeline and of the metrics collector activity |
| [analysis/](/docs/analysis/) | Investigations: descriptor transformations, the manifest v2 specification, documentation gaps, the RegDef v2 extensions |

## Tests

| Folder | What it holds |
| --- | --- |
| [test-cases/](/docs/test-cases/README.md) | The manual and end-to-end test cases of each feature, one page per feature |

Documentation of a behaviour changes in the same pull request as the code that changes the
behaviour.
