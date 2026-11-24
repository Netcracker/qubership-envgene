# Ansible compatibility specification and design

- [Purpose and decisions](#purpose-and-decisions)
- [Sources and rendering contracts](#sources-and-rendering-contracts)
- [Static compatibility analysis](#static-compatibility-analysis)
- [Reporting and verification](#reporting-and-verification)

## Purpose and decisions

TPL-6 reviews legacy Ansible expressions against the current EnvGene rendering contract after applying supported
compatibility transformations. Filters and raw blocks remain permitted. An incompatible or unconfirmed expression
produces Information / Review, never an automatic rewrite or a filter-prohibition Fix.
The existing prohibited Jinja statements and loop checks keep their classifications.

The check establishes compatibility with known handlers, not successful generation for arbitrary runtime inputs.
TPL-4 remains responsible for presence protection. No template, filter, lookup, or external command is executed.
The linter does not read process environment values, lookup targets, or remote repositories.

## Sources and rendering contracts

The compatibility collector retains existing parsed template sources and inspects potential Ansible expressions
in repository-local YAML and Jinja configuration under `templates/`, `environments/`, and `configuration/`.
Root `description_template*.yml` and `description_template*.yaml` are excluded as separate GSF/CI inputs.
Safe path checks reject external and `.git` targets, cyclic links, and directory symlink traversal.

Four rendering contracts are distinguished:

- `envgene`: the full renderer applies compatibility transformations and registers `to_nice_yaml` and `urlsplit`.
- `custom_jinja`: registered EnvGene filters are available without compatibility transformations.
- `jinja`: standard Jinja filters are available without EnvGene transformations or custom filters.
- `unknown`: the source's consumer or rendering stage is not established.

Full `.yml.j2` and `.yaml.j2` sources under `templates/` and ordinary Registry/Application Definition YAML use `envgene`.
All files with this confirmed contract are analyzed without requiring a legacy marker.
Bare `.j2` ParameterSets use `jinja`. Other bare `.j2` sources remain `unknown` unless their stage is established.
Recognized ordinary environment descriptor path scalars use `jinja`.
Cloud override scalars use `envgene`. Namespace overrides require both `custom_jinja` for early name discovery
and `envgene` for later object rendering. Other override contexts remain `unknown`.
Unclassified ordinary YAML is inspected only for legacy Ansible syntax, with an unknown consumer contract.
This additional scope does not broaden TPL-4 or ordinary TPL-6 statement checks.
Descriptor checks analyze decoded scalar text rather than reproducing whole-object serialization.
They do not establish compatibility of serialization-specific quoting, escaping, or cross-scalar interactions.

Contracts follow [renderer entry points](/scripts/build_env/render_config_env.py),
[ParameterSet loading](/scripts/build_env/build_env.py), and
[filter registration](/scripts/build_env/jinja/jinja.py).

## Static compatibility analysis

Apply the exact supported patterns from
[EnvGene compatibility processing](/scripts/build_env/jinja/replace_ansible_stuff.py) to an analysis copy for `envgene`:
`ansible.builtin.to_nice_yaml`, the supported single-quoted `ansible.builtin.env` lookup, and standalone underscore names.
Preserve original line counts. Do not strip a document prefix or change checked files.
Parse the resulting representation without compiling or rendering it.

Review unsupported legacy lookup forms, remaining Ansible-specific calls or filters, and filters absent from the
known rendering environment. Check the static argument contract of the two EnvGene filters:
`to_nice_yaml` takes no extra arguments, and `urlsplit` accepts at most one `part` argument.
Dynamic argument expansion remains uncertain. Standard Jinja filters are permitted without a full type analysis.
Unknown rendering stages in the selected configuration receive Review without assuming an external plugin installation.

Raw contents and Jinja comments do not become executable expressions. If a compatibility transformation changes
literal template text, raw contents, or a quoted Jinja string, report Review because passthrough changes before Jinja.
Changes confined to Jinja comments need no finding. Check executable Jinja in YAML comments of full-file templates
because YAML parsing occurs after rendering. Syntax failures after compatibility processing receive Review.

## Reporting and verification

Keep one compatibility Review per physical file and original source line. Descriptor positions identify the selected
scalar opening line. Messages identify the contract problem without copying values, variable names, custom filter names,
lookup paths, raw expressions, or parser exceptions. Existing HTML, JSON, console, and exit-code contracts are retained.
Disabling TPL-6 bypasses its extra compatibility collection and analysis.

Regression tests cover supported and unsupported forms, quote and argument differences, rendering stages, raw and string
boundaries, YAML versus Jinja comments, redaction, descriptor positions, safe paths, and disabled rules.
Synthetic fixtures demonstrate compatible transformations and Review cases. A read-only corpus run reports aggregates
and private local file locations without committing or publishing repository data.
