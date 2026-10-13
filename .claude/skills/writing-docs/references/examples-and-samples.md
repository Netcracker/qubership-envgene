# Object examples and sample files

How to write validated object examples inside docs, and how to build copyable sample file sets under
`docs/samples/`. Both derive from the authoritative schemas, never from guesswork.

- [Object examples and sample files](#object-examples-and-sample-files)
  - [Object examples in documentation](#object-examples-in-documentation)
    - [Source of truth for object schemas](#source-of-truth-for-object-schemas)
      - [Rules](#rules)
      - [How much of the object to show](#how-much-of-the-object-to-show)
      - [❌ Incorrect - invented fields and unnecessary noise](#-incorrect---invented-fields-and-unnecessary-noise)
      - [✅ Correct - focused snippet, validated field names, omissions annotated](#-correct---focused-snippet-validated-field-names-omissions-annotated)
  - [Sample files in docs/samples/](#sample-files-in-docssamples)
    - [Samples are mandatory](#samples-are-mandatory)
    - [Feature-scoped sample folders](#feature-scoped-sample-folders)
    - [One sample, one home](#one-sample-one-home)
    - [Samples are generation-ready](#samples-are-generation-ready)
    - [Placeholder values](#placeholder-values)

## Object examples in documentation

### Source of truth for object schemas

**CRITICAL: Never invent object structures. Always derive examples from authoritative sources.**

The two authoritative sources are:

- **`docs/envgene-objects.md`** - human-readable descriptions, field explanations, and canonical examples for all EnvGene objects
- **`schemas/`** - JSON Schema files that define required fields, allowed values, and types

#### Rules

1. **Before writing any YAML/JSON example** for an EnvGene object, read the corresponding entry in `docs/envgene-objects.md` AND the matching schema file under `schemas/`.
2. **Validate every example against the schema**: all fields marked `"required"` in the schema
   must be present. No fields may be included that do not exist in the schema (unless
   `additionalProperties: true`).
3. **Do not guess**: if an object is not described in `docs/envgene-objects.md` and has no schema file, write explicitly:

   > No schema or description found for this object in `docs/envgene-objects.md` or `schemas/`. Cannot provide a validated example.

4. **Do not add fictional fields** such as `type:` or `applications:` to objects that have no such fields in their schema.
5. **Use real field names**: cross-check field names and allowed enum values against the schema. Do not invent field names based on intuition.

#### How much of the object to show

In tutorials and how-to guides, show only the **relevant part** of the object, not the full structure. Use `# ...` comments to signal omitted fields so the reader knows the snippet is intentionally incomplete.

- **Reference docs** → show the full object.
- **Tutorials / how-to guides** → show only the fields being explained. Collapse the rest with `# ...`.

This keeps examples focused on the concept being taught and avoids becoming outdated when unrelated fields change.

#### ❌ Incorrect - invented fields and unnecessary noise

```yaml
# Namespace template - WRONG: invented fields, full object shown in tutorial context
name: "{{ current_env.name }}-bss"
type: namespace          # does not exist in namespace.schema.json
applications:            # does not exist in namespace.schema.json
  - name: "Cloud-BSS"
credentialsId: ""
isServerSideMerge: false
cleanInstallApprovalRequired: false
mergeDeployParametersAndE2EParameters: false
deployParameterSets:
  - "bss"
```

#### ✅ Correct - focused snippet, validated field names, omissions annotated

```yaml
# Namespace template - only the relevant section is shown
---
name: "{{ current_env.environmentName }}-bss"
# ... other required fields (see schemas/namespace.schema.json) ...
profile:
  name: dev-bss-override
  baseline: dev
# ... deployParameterSets, e2eParameters, etc. ...
```

---

## Sample files in docs/samples/

Sample file sets under `docs/samples/` are copyable template-repository and instance-repository files.
This section covers the files. Inline YAML snippets inside docs are covered by
[Object examples in documentation](#object-examples-in-documentation) above.

**Scope:** All rules in this section apply to **new and modified samples only**. Changing a file in an
existing set re-triggers the file-level rules (generation-ready checks, placeholder values) for the
changed files only. Folder-level items (subfolder names, index entries) apply only when you create or
restructure the folder. Existing sample sets are not affected until touched.

---

### Samples are mandatory

**A how-to guide whose steps involve authoring or editing repository files, or a feature doc that
introduces user-facing configuration, ships with working sample files in the same PR. Prose and inline
snippets alone are not enough.**

Link existing samples when they already cover the scenario: the linked set holds the files and the states
that the guide's steps use. Add new ones otherwise. User-facing configuration means files or fields that
users author in template or instance repositories.

❌ **INCORRECT:**

- A how-to guide that describes configuration structure only in prose and inline snippets.
- A feature doc that introduces a new user-facing configuration file with no copyable sample.

✅ **CORRECT:**

- A how-to guide plus `docs/samples/<feature>/` holding the files it references, cross-linked both ways.
- A how-to guide that links samples already present under `docs/samples/`.

**Scope:** Applies to **new how-to guides, new feature docs, and new sections that introduce
configuration only**.

**Why:** Samples are executable documentation. They surface defects prose hides - invalid fields, name
mismatches, unresolvable references - and give the reader a verified starting point.

---

### Feature-scoped sample folders

**Samples for one feature live in one folder, `docs/samples/<feature>/`, with the template-repository and
instance-repository parts side by side.**

Name the folder after the feature, matching the `docs/features/` doc name where one exists.

```text
docs/samples/<feature>/
├── template-repository/    # Template repository files
└── instance-repository/    # Instance repository files
```

- Create only the subfolders that have content.
- Inside the two subfolders, mirror the real repository paths
  (`template-repository/templates/env_templates/...`, `instance-repository/environments/...`). For
  path segments the reader renames, use concrete instance names in the style of the existing samples
  (`cluster-01`, `env-01`) - not angle-bracket tokens, and not bare contract-looking segments
  (`cluster`, `env`) that read as mandatory path elements.
- Express variants of one file as separate sample instances, never as suffixed filenames. Alternative
  inventories become separate environment folders (`env-01/`, `env-02/`), each holding a real
  `env_definition.yml`. Annotate what each variant shows in the sample itself (for the
  inventories, the `description` field).
- The folder holds every feature-specific state the guide references. A state identical to a
  generic-tree baseline, or to a file homed in another feature folder, is linked instead of copied. A
  state that differs is a separate sample instance.
- The folder has no readme. Usage steps and target paths live in the guide that references the
  samples.
- Add the folder to the Examples & Samples section of both index readmes (see
  [Doc index updates](doc-structure.md#doc-index-updates)) and add a short section for it to the samples hub readme
  `/docs/samples/README.md`.
- The generic layout trees (`template-repository/`, `instance-repository/`) stay minimal baselines and
  do not accumulate feature samples.

**Why:** A reader following a guide needs the full set in one place, including variants a single
canonical tree cannot express. Mirrored paths and shared subfolder names keep the set readable in the
vocabulary the repository already uses.

---

### One sample, one home

**A sample artifact lives in exactly one place under `docs/samples/` - not copied between a feature
folder and the generic layout trees, between two feature folders, or within one folder.**

Files that genuinely differ are variants, not copies. When a feature folder becomes the home of a
sample, delete the copy elsewhere and update links.

**Why:** Duplicated samples drift apart, and readers cannot tell which copy is authoritative.

---

### Samples are generation-ready

**A sample set works when copied as instructed. The checks below define acceptance: filenames, object
names, and cross-references satisfy the resolution rules of the code.**

No CI job validates sample files against the schemas. Run the checks manually.

Before you declare a sample set done:

1. Validate every file against its JSON Schema in `schemas/`, as
   [Object examples in documentation](#object-examples-in-documentation) prescribes for snippets.
   Field types matter: `[]` and `{}` are not interchangeable. A schema pass is necessary, not
   sufficient - the schemas allow additional properties, so also check field names against the object
   reference. For `.j2` files, check the rendered shape against the target schema.
2. Check names the code resolves by convention: the template descriptor filename equals
   `envTemplate.name`, BG Domain namespace names equal `template_override.name` values, and so on.
   Confirm each convention in the code (see [Verify, don't fabricate](content-integrity.md#verify-dont-fabricate)).
3. Exclude system-generated fields (for example `generatedVersions`) from files the reader copies.
4. Exclude references to resources the sample set does not provide (for example a `cloudPassport`
   name without a passport file), or state where they come from in the referencing guide or in a
   comment inside the sample file.

**Why:** A sample that fails generation is worse than no sample. The reader assumes their own mistake
and loses time debugging shipped configuration.

---

### Placeholder values

**Sample values are obviously fake and self-describing. Never use realistic-looking secrets.**

- Secret values: self-describing placeholders such as `dbaas-password` or `token-placeholder-123`, or
  Credentials of `type: external`. No opaque strings that could pass for real tokens. Credential IDs
  (`bgdomain-cred`) are names, not secret values - normal naming rules apply.
- Hosts and URLs: reserved example domains (`example.com`, `k8s.example.local`).
- Substitution slots: angle-bracket tokens following the vocabulary of the samples hub readme
  (`<cluster-name>`, `<environment-name>`, `<paramset>`).

**Why:** A realistic-looking secret in a sample trains readers to paste real ones and trips secret
scanners. Self-describing placeholders show which value goes where without a legend.
