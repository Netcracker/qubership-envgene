# Templating Rules

Rules for **Jinja templates and macros** — how templates derive values and render safely.
Source: [configuration-standard.md](../configuration-standard.md)

Cross-document dependencies: TPL-7 → VAL-3 (Correctness Rules), TPL-10 → SEC-1 (Correctness Rules).

---

### TPL-1 - Jinja lives only in `.j2` templates (MUST)

A `.j2` template may use Jinja. An instance ParameterSet, a Cloud Passport, and a Credential file are plain YAML with no Jinja.

```yaml
# OK - templates/.../parameters.yml.j2
MY_NAMESPACE: "{{ current_env.name }}-core"
# Not OK - the same Jinja in an instance file (environments/.../parameters.yml)
MY_NAMESPACE: "{{ current_env.name }}-core"
```

### TPL-2 - Override at a layer, not through Jinja plumbing (MUST)

To change a value at a layer, place the value at that layer. Do not add Jinja plus `additionalTemplateVariables` plus interpolation to push a value down. Interpolation composes a string, it does not pass a key through unchanged.

```yaml
# Not OK - the template re-emits a key just to pass it through
# parameters.yml.j2:  LOG_LEVEL: "{{ LOG_LEVEL }}"   with additionalTemplateVariables LOG_LEVEL: info
# OK - set the value at the layer, no template logic
# environments/<cluster>/<env>/parameters.yml:  LOG_LEVEL: info
```

### TPL-3 - Default at a layer, not a Jinja default (MUST)

Put a default value in a shallower layer and override the delta deeper. Use a Jinja conditional only for genuine branching, not to supply a missing default.

```yaml
# Not OK - default hidden in template logic
TIMEOUT: "{{ TIMEOUT | default('30s') }}"
# OK - default at the template layer, optional override at env
# template parameters.yml.j2:  TIMEOUT: 30s
# env parameters.yml (optional):  TIMEOUT: 60s
```

### TPL-4 - A reference never fails on a missing value (SHOULD)

A value that can be absent is wrapped with `| default(...)`, so a missing input renders empty instead of failing generation.

```yaml
# Not OK - fails when FEATURE_A is absent
ENABLED: "{% if FEATURE_A == 'on' %}true{% else %}false{% endif %}"
# OK - safe on absence
ENABLED: "{% if FEATURE_A | default('') == 'on' %}true{% else %}false{% endif %}"
```

### TPL-5 - No per-level presence guards (SHOULD)

Do not guard a nested access with an `is defined` check at each level. EnvGene resolves a missing key at any depth of a path to empty rather than an error, so a per-level guard wall defends against a failure that cannot happen. Read the value with one trailing `| default(...)` (see TPL-4), which covers the whole path, and use a single `is defined` on the full path only to branch on whether an optional block is present.

```yaml
# Not OK - a guard at each level, standing in for a failure that cannot occur
DR_MODE: "{% if current_env.additionalTemplateVariables is defined and current_env.additionalTemplateVariables.drParameters is defined %}{{ current_env.additionalTemplateVariables.drParameters.mode }}{% endif %}"
# OK - one trailing default covers every missing level of the path
DR_MODE: "{{ current_env.additionalTemplateVariables.drParameters.mode | default('') }}"
# OK - a single presence test to branch on an optional block
{% if current_env.additionalTemplateVariables.drParameters is defined %}
DR_ENABLED: true
{% endif %}
```

### TPL-6 - Keep template logic small (SHOULD)

Use `if`, `elif`, `else`, and the filters `default`, `join`, `upper`, and `lower`. Use a `for` loop only to iterate a genuinely dynamic list. Never use `macro`, `include`, `import`, `extends`, `block`, `raw`, or a custom filter — reuse comes from template composition. Deeply nested logic is a signal the value should be set by placement, not by rendering.

```yaml
# Not OK - macro and include
# {% macro url(h) %}...{% endmacro %}   {% include "shared.j2" %}
# OK - a single conditional
FEATURE: "{% if SITE | default('') == 'onsite' %}on{% else %}off{% endif %}"
```

### TPL-7 - Build URLs from the Cloud Passport host (MUST)

Compose a service URL from the passport host value (`CLOUD_PUBLIC_HOST`), not from a hardcoded cluster hostname. The template appends the path to the host.

See also: VAL-3 (Correctness Rules) — no trailing slash on URLs.

```yaml
# Not OK - hardcoded cluster hostname
MY_SERVICE_URL: https://my-service.cluster-01.example.com
# OK - built from the passport host
MY_SERVICE_URL: "https://my-service.{{ CLOUD_PUBLIC_HOST }}"
```

### TPL-8 - Protect Helm passthrough (MUST)

A token meant for Helm, not EnvGene, is wrapped in `{% raw %}` so EnvGene does not evaluate it. EnvGene renders its own `{{ }}` and leaves Helm's for the chart.

```yaml
# Not OK - EnvGene evaluates a Helm token and breaks it
RELEASE: "{{ .Release.Name }}"
# OK - protected for Helm
RELEASE: "{% raw %}{{ .Release.Name }}{% endraw %}"
```

### TPL-9 - Every branch renders valid YAML (SHOULD)

Each branch of a conditional emits well-formed YAML of the target shape. No branch leaves a half-written key or a broken document.

```yaml
# Not OK - the empty branch leaves a dangling key
TIMEOUT:{% if HAS_TIMEOUT %} 30s{% endif %}
# OK - each branch emits a complete value
TIMEOUT: "{% if HAS_TIMEOUT | default('') %}30s{% else %}10s{% endif %}"
```

### TPL-10 - No secret in a template (SHOULD)

A template holds no secret literal and no secret in a comment. Secrets live in Credential objects and are referenced (see SEC-1 in Correctness Rules).

```yaml
# Not OK - a secret baked into a template value
DB_PASSWORD: "s3cr3t-{{ current_env.name }}"
# OK - reference a credential
DB_PASSWORD: ${creds.get("db-cred").password}
```

### TPL-11 - No hardcoded derivable values (MUST)

Do not author a literal for a value EnvGene derives — the environment name, cloud and cluster names, cluster hosts and ports. Read it from the context variable or macro instead (see [template macros](/docs/template-macros.md)). Build a URL from the Cloud Passport host per TPL-7. TPL-12 to TPL-14 unpack the common namespace and solution cases.

```yaml
# Not OK - literals for derived values
DEPLOYMENT_ENV: env-1
CLOUD_NAME: cluster-01
# OK - read from the context
DEPLOYMENT_ENV: "{{ current_env.name }}"
CLOUD_NAME: "{{ current_env.cloud }}"
```

### TPL-12 - Reference the current namespace with a macro (SHOULD)

Under TPL-11, when a value must contain the current namespace's name, read it from `${NAMESPACE}`, which EnvGene resolves from the rendered Namespace object. Do not rebuild the name by concatenation such as `current_env.name` plus a postfix literal, which re-implements the naming convention and drifts when the scheme changes.

```yaml
# OK
PG_HOST: "pg-patroni.${NAMESPACE}"
# Not OK - the same name rebuilt by hand
PG_HOST: "pg-patroni.{{ current_env.name }}-oss"
```

### TPL-13 - Gate on app presence, not on a toggle (SHOULD)

Under TPL-11, emit a parameter block only when an application is really in the solution by testing `current_env.solution_structure`, so presence follows the resolved composition. Do not gate the same decision on a hand-maintained `additionalTemplateVariables` toggle, which an operator must keep in sync with the Solution Descriptor and which drifts. Combining presence with a real feature toggle is fine.

```yaml
# OK - presence derived from the solution
{% if 'billing-app' in current_env.solution_structure %}
BILLING_ENABLED: true
{% endif %}
# Not OK - a hand-kept flag standing in for presence
{% if current_env.additionalTemplateVariables.billing_enabled %}
BILLING_ENABLED: true
{% endif %}
```

### TPL-14 - Resolve a namespace by deploy-postfix, do not rebuild it (SHOULD)

Under TPL-11, when a value must contain the current namespace's name or a neighbor's, look it up by its deploy-postfix rather than rebuilding it by concatenation or carrying it in an `additionalTemplateVariables` key. The target is a late-resolving calculator macro keyed by deploy-postfix (see TPL-15), which resolves after every namespace is rendered and so never sees a neighbor as Null. That macro is not yet available, so until it ships resolve a neighbor through the documented Jinja path `current_env.solution_structure['<app>']['<deploy-postfix>'].namespace`, which returns Null when the neighbor is not yet rendered. The host suffix stays under TPL-7.

```yaml
# Not OK - a neighbor namespace name rebuilt by hand
OSS_NAMESPACE: "{{ current_env.name }}-oss"
# OK (target) - a late-resolving macro keyed by deploy-postfix, exact syntax to be finalized
OSS_NAMESPACE: "${namespace_map('oss')}"
# OK (today) - documented Jinja interim, keyed by application then deploy-postfix
OSS_NAMESPACE: "{{ current_env.solution_structure['oss-app']['oss'].namespace }}"
```

### TPL-15 - Prefer a macro over a Jinja expression (SHOULD)

When the same value is available as a calculator macro (`${...}`) and as a Jinja expression (`{{ ... }}`), prefer the macro. A macro needs no `.j2` template, resolves late so a cross-reference reflects the deployed state instead of a generation-time snapshot, and is a stable contract. Reach for Jinja when the value must be fixed at generation, or when no macro exposes it. TPL-12 and TPL-14 are the namespace cases of this preference.

```yaml
# OK - a macro, resolved late in a plain ParameterSet
PG_HOST: "pg-patroni.${NAMESPACE}"
# Not OK - Jinja recomputes the same name at generation and needs a .j2
PG_HOST: "pg-patroni.{{ current_env.name }}-oss"
```

### TPL-16 - Edit inputs, not generated output (SHOULD)

A generated object — the Effective Set, a generated `cloud.yml` or namespace file, anything marked auto-generated — is overwritten on the next generation. To change it, edit the template or the inventory that produces it, not the generated file.

```yaml
# Not OK - hand-editing a generated file (overwritten next run)
# environments/<cluster>/<env>/effective-set/...   or a generated cloud.yml
# OK - edit the input that produces it
# templates/.../parameters.yml.j2   or   environments/.../Inventory/parameters/...
```
