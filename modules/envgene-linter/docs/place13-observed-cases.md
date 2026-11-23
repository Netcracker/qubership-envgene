# PLACE-13 cases observed in instance repositories

The scan covered 747 environment definitions under local instance repositories. It counted where deploy
parameters sit. It did not copy parameter values, application names, or key names into this note.

Helm charts and `values.schema.json` files are absent from those repositories, so the scan cannot say
whether a key is accepted. Acceptance is a property of the charts still to be written. Until those charts
exist, every scenario below is a stub. The steps are not in the Cucumber suite. The channel is the linter
report (`envgene-linter-report.html` and `envgene-linter-report.json`), produced by `envgene-linter check`
with `--helm-parameter-catalog`.

Names in angle brackets are placeholders for that future data. They are not applications or keys that
already exist.

## What the repositories actually do

| Shape | How often |
| --- | --- |
| Environment binds both a cloud target and at least one namespace target | 444 |
| Environment binds only namespace targets | 172 |
| Environment binds only the cloud target | 29 |
| Parameter file use with a plain `parameters` map | 1030 |
| Parameter file use with an `applications` section | 657 |
| `applications` section on a namespace target | 623 |
| `applications` section on the cloud target | 34 |
| Environments whose widest namespace holds 3 or more applications | 190 |
| Same key present at cloud and at namespace | 165 keys |
| Those overlapping keys have different values | 20 |
| Those overlapping keys have the same value | 145 |
| File that names 2 or more applications | 229 |
| Such a file has at least one key present on only one of those applications | 214 |
| Cluster parameter file used by 10 or more environments | 18 files |
| Repository-level parameter file used by 10 or more environments | 16 files |
| Environments with no solution descriptor applications | about 550 |
| Plain values whose text looks like a credential macro | 1318 |

Two consequences for the charts:

- A namespace often holds many applications. A useful chart set needs several applications in one
  `deployPostfix`, and their schemas must not all list the same keys.
- Authors already put most narrow keys in `applications[]` on a namespace file. The misplaced case is a
  key left in the plain `parameters` map of a cloud or namespace file.

The scan did not count namespaces that hold exactly one application. Of the environments that bind a
namespace, 190 have a widest namespace of three or more, so the rest are smaller, but one and two are not
split here. The single-application namespace is still required below, because that is the boundary where a
plain namespace key is already narrow enough.

## Cases

Levels, wide to narrow, are `cloud`, `app@cloud`, `ns`, `app@ns`. A key that every reached application
accepts stays where it is. A key that only a subset accepts moves to `app@ns` for each accepting
application, unless a nearer level already sets a different value, or the source file is shared and the
sharing environments do not agree on one owner. A key that nobody accepts is a delete candidate. The
linter does not edit files.

1. Cloud key in a plain `parameters` map. Every application in the solution descriptor accepts it. No
   PLACE-13 finding.
2. Namespace key in a plain `parameters` map. That namespace's solution descriptor lists one application,
   and that application accepts the key. No PLACE-13 finding.
3. Key stored only under `applications[]` for one application on a namespace ParameterSet, and that
   application accepts it. No PLACE-13 finding. This is the common authoring shape: 623 of 657
   `applications` sections sit on a namespace target, and 214 of 229 multi-application files already
   isolate at least one key on a single application.
4. Key stored under `applications[]` on the cloud target (`app@cloud`), and that one application accepts
   it. No PLACE-13 finding. The scan found 34 such sections. All-accept does not move the key down to the
   namespace.
5. Plain cloud or namespace key. Several applications are in scope, only a subset accepts the key, and no
   nearer level sets a different value. Fix for each accepting application, aimed at `app@ns`.
6. Same key at cloud and at namespace, values differ, and only a subset would otherwise accept the wider
   value. Review. The scan found 20 overlapping keys with different values. A move would override the
   nearer value.
7. Same key at cloud and at namespace, values are equal, and only a subset accepts the key. Fix. The scan
   found 145 overlapping keys with the same value. An equal nearer value does not block the move.
8. Plain key in a cluster or repository ParameterSet used by more than one environment. Every sharing
   environment agrees on the same accepting applications. Fix on that shared file. The file stays shared.
   The scan found 18 cluster files and 16 repository-level files used by 10 or more environments. It
   cannot tell which of them would agree, because the schemas are missing.
9. Same shared-file shape, but the sharing environments would name different accepting applications.
   Review. One edit cannot send the key to two owners.
10. Environment with no solution descriptor. Cloud and namespace keys produce a skipped check, not an
    accept or reject finding. An `applications[]` entry can still be judged for that one application.
    About 550 environments have no solution descriptor applications.
11. No reached application accepts the key. Review, and the review calls the key a delete candidate. The
    repositories cannot show this. The generated schemas must refuse one key on purpose.
12. A reached application has a service with no `values.schema.json`. Review, and the review says
    acceptance cannot be decided. The repositories cannot show this. One generated application must ship
    an unresolved service.
13. The catalog marks the key `internal` or `envSpecific`. No PLACE-13 finding, even when other reached
    applications do not list the key.
14. The key is a child of a map with `additionalProperties: true`. That application accepts the key.
15. The same key is set to two different credential-macro strings at two levels. PLACE-13 compares the
    strings as text, so this is a review, the same as any other different value. The scan found 1318
    plain values whose text looks like a macro. It did not count how many of the 20 differing overlaps
    are macros.
16. The ParameterSet writes the key as `<alias>.<key>`, and the catalog lists only the subchart-local
    `<key>`. The application does not count as accepting. Generate both forms on purpose, and keep a
    matching pair as the control.

A passport contract key is out of PLACE-13. PLACE-4 owns it. Generated data may include one, and the
PLACE-13 section of the report stays empty for it.

## Acceptance criteria

- Given a cloud deploy key and a catalog where every application in the solution descriptor accepts that
  key, the linter report has no PLACE-13 finding for the key.
- Given a namespace whose solution descriptor lists one application, and a namespace key that application
  accepts, the linter report has no PLACE-13 finding for the key.
- Given the key stored only under `applications[]` for one application on a namespace ParameterSet, and
  that application's catalog accepts the key, the linter report has no PLACE-13 finding for the key.
- Given the key stored under `applications[]` for one application on a cloud ParameterSet, and that
  application's catalog accepts the key, the linter report has no PLACE-13 finding for the key.
- Given a cloud or namespace key accepted by one or more, but not all, applications in that scope, and no
  nearer level sets a different value, the linter report has a PLACE-13 Fix for each accepting
  application, and each fix names `app@ns`.
- Given the same key at cloud and namespace with different values, and only a subset of applications
  accepting the wider key, the linter report has a PLACE-13 Review and does not recommend the move.
- Given the same key at cloud and namespace with equal values, and only a subset of applications
  accepting it, the linter report has a PLACE-13 Fix for each accepting application.
- Given a ParameterSet file bound by two environments that agree on the same accepting applications, the
  linter report has a PLACE-13 Fix and the shared file remains the source.
- Given a ParameterSet file bound by two environments that would assign different accepting applications,
  the linter report has a PLACE-13 Review for each environment and does not recommend one move.
- Given an environment with no solution descriptor, a cloud deploy key produces a PLACE-13 skipped check
  and no accept or reject finding.
- Given a key no reached application accepts, the linter report has a PLACE-13 Review that names the key
  as a delete candidate.
- Given a reached application whose catalog lists an unresolved service, the linter report has a PLACE-13
  Review and does not decide acceptance.
- Given a key the catalog marks `internal` or `envSpecific`, the linter report has no PLACE-13 finding
  for the key.
- Given a key under a catalog map with `additionalProperties: true`, PLACE-13 treats that application as
  accepting the key.
- Given two levels set the same key to different credential-macro strings, the linter report treats them
  as different values and emits a PLACE-13 Review when a move would otherwise apply.
- Given the ParameterSet key uses an umbrella alias prefix and the catalog lists the key without that
  prefix, the linter report does not treat the application as accepting the key.

## Scenarios

```gherkin
# Stub. Every step below is new. These scenarios are not part of the pipeline Cucumber suite.
# The channel is the linter report from `envgene-linter check --helm-parameter-catalog`.
# Angle-bracket tokens are data that does not exist yet.

# why: case 1. A wide key is already valid for every reached application.
Scenario: a cloud key accepted by every reached application is left in place
  Given an environment binds a cloud deploy ParameterSet
  And the solution descriptor lists "<application-a>" and "<application-b>" in one namespace
  And the Helm parameter catalog says both applications accept "<deploy-key>"
  And the cloud ParameterSet sets "<deploy-key>"
  When the linter checks the environment with that catalog   # NEW STEP NEEDED
  Then the linter report has no PLACE-13 finding for "<deploy-key>"   # NEW STEP NEEDED

# why: case 2. A namespace of one application is already narrow enough.
Scenario: a namespace key is kept when that namespace has one accepting application
  Given an environment binds a namespace deploy ParameterSet
  And the solution descriptor lists only "<application-a>" in that namespace
  And the catalog says "<application-a>" accepts "<deploy-key>"
  And the namespace ParameterSet sets "<deploy-key>"
  When the linter checks the environment with that catalog   # NEW STEP NEEDED
  Then the linter report has no PLACE-13 finding for "<deploy-key>"   # NEW STEP NEEDED

# why: case 3. The common shape in the repositories. The key is already on one application.
Scenario: a key already stored on one namespace application is not moved again
  Given a namespace ParameterSet has an applications entry for "<application-a>" only
  And that entry sets "<deploy-key>"
  And the catalog says "<application-a>" accepts "<deploy-key>"
  When the linter checks the environment with that catalog   # NEW STEP NEEDED
  Then the linter report has no PLACE-13 finding for "<deploy-key>"   # NEW STEP NEEDED

# why: case 4. Thirty-four application sections sit on the cloud target. All-accept leaves them there.
Scenario: a key already stored on one cloud application is not moved to the namespace
  Given a cloud ParameterSet has an applications entry for "<application-a>" only
  And that entry sets "<deploy-key>"
  And the catalog says "<application-a>" accepts "<deploy-key>"
  And "<application-a>" is deployed in a namespace
  When the linter checks the environment with that catalog   # NEW STEP NEEDED
  Then the linter report has no PLACE-13 finding for "<deploy-key>"   # NEW STEP NEEDED

# why: case 5. The misplaced wide key. One of several applications accepts it.
Scenario: a wide key accepted by one of several applications is a move
  Given an environment binds a cloud deploy ParameterSet that sets "<deploy-key>"
  And the solution descriptor lists "<application-a>" and "<application-b>" in one namespace
  And only "<application-a>" accepts "<deploy-key>"
  And no nearer level sets "<deploy-key>"
  When the linter checks the environment with that catalog   # NEW STEP NEEDED
  Then the linter report has a PLACE-13 Fix for "<deploy-key>"   # NEW STEP NEEDED
  And the fix names "<application-a>" and "app@ns"   # NEW STEP NEEDED

# why: case 5. Two consumers each get their own move. One refusing application stays out of the fix.
Scenario: a wide key accepted by two of three applications produces two moves
  Given an environment binds a namespace deploy ParameterSet that sets "<deploy-key>"
  And that namespace lists "<application-a>", "<application-b>", and "<application-c>"
  And "<application-a>" and "<application-b>" accept "<deploy-key>"
  And "<application-c>" does not accept "<deploy-key>"
  And no nearer level sets "<deploy-key>"
  When the linter checks the environment with that catalog   # NEW STEP NEEDED
  Then the linter report has a PLACE-13 Fix for "<deploy-key>" naming "<application-a>"   # NEW STEP NEEDED
  And the linter report has a PLACE-13 Fix for "<deploy-key>" naming "<application-b>"   # NEW STEP NEEDED
  And the linter report has no PLACE-13 Fix for "<deploy-key>" naming "<application-c>"   # NEW STEP NEEDED

# why: case 6. Twenty overlapping keys in the scan had different values.
Scenario: a nearer different value blocks the move
  Given the cloud ParameterSet sets "<deploy-key>" to one value
  And the namespace ParameterSet sets "<deploy-key>" to another value
  And only "<application-a>" accepts "<deploy-key>"
  When the linter checks the environment with that catalog   # NEW STEP NEEDED
  Then the linter report has a PLACE-13 Review for the cloud "<deploy-key>"   # NEW STEP NEEDED
  And the review does not recommend moving it   # NEW STEP NEEDED

# why: case 7. Most overlapping keys had the same value, so the move does not change it.
Scenario: an equal nearer value still allows the move
  Given the cloud and namespace ParameterSets set "<deploy-key>" to the same value
  And only "<application-a>" accepts "<deploy-key>"
  When the linter checks the environment with that catalog   # NEW STEP NEEDED
  Then the linter report has a PLACE-13 Fix for the cloud "<deploy-key>"   # NEW STEP NEEDED

# why: case 8. Shared files are common. Agreement still allows one move on the shared file.
Scenario: sharing environments that agree on one owner allow a move
  Given one cluster ParameterSet is bound by two environments
  And that file sets "<deploy-key>"
  And in both environments only "<application-a>" accepts "<deploy-key>"
  When the linter checks both environments with that catalog   # NEW STEP NEEDED
  Then the linter report has a PLACE-13 Fix for "<deploy-key>" in each environment   # NEW STEP NEEDED
  And both fixes name the same shared file   # NEW STEP NEEDED

# why: case 9. The same shared file is a review when the owners differ.
Scenario: sharing environments that disagree on the owner are review only
  Given one cluster ParameterSet is bound by two environments
  And that file sets "<deploy-key>"
  And the first environment accepts "<deploy-key>" only on "<application-a>"
  And the second environment accepts "<deploy-key>" only on "<application-b>"
  When the linter checks both environments with that catalog   # NEW STEP NEEDED
  Then the linter report has a PLACE-13 Review for "<deploy-key>" in each environment   # NEW STEP NEEDED
  And neither review recommends a move   # NEW STEP NEEDED

# why: case 10. Hundreds of environments have no solution descriptor applications.
Scenario: a missing solution descriptor does not invent an owner
  Given an environment binds a cloud deploy ParameterSet
  And the environment has no solution descriptor
  When the linter checks the environment with a Helm parameter catalog   # NEW STEP NEEDED
  Then the linter report has a PLACE-13 skipped check for that environment   # NEW STEP NEEDED
  And it has no PLACE-13 accept or reject finding for the cloud keys   # NEW STEP NEEDED

# why: case 11. Schema rejection cannot be read from the repositories. The chart must refuse the key.
Scenario: a key no application accepts is a delete candidate
  Given a cloud ParameterSet sets "<rejected-key>"
  And the solution descriptor lists "<application-a>" and "<application-b>"
  And neither catalog accepts "<rejected-key>"
  When the linter checks the environment with that catalog   # NEW STEP NEEDED
  Then the linter report has a PLACE-13 Review for "<rejected-key>"   # NEW STEP NEEDED
  And the review calls it a delete candidate   # NEW STEP NEEDED

# why: case 12. One generated application must ship a service without a schema.
Scenario: an unresolved service blocks the verdict
  Given an applications entry sets "<deploy-key>" for "<application-unresolved>"
  And the catalog for "<application-unresolved>" lists a service with no values schema
  When the linter checks the environment with that catalog   # NEW STEP NEEDED
  Then the linter report has a PLACE-13 Review for "<deploy-key>"   # NEW STEP NEEDED
  And the review says acceptance cannot be decided   # NEW STEP NEEDED

# why: case 13. Internal keys are skipped even when other applications do not list them.
Scenario: an internal key is skipped
  Given a cloud ParameterSet sets "<internal-key>"
  And the catalog marks "<internal-key>" internal for "<application-a>"
  And "<application-b>" does not list "<internal-key>"
  When the linter checks the environment with that catalog   # NEW STEP NEEDED
  Then the linter report has no PLACE-13 finding for "<internal-key>"   # NEW STEP NEEDED

# why: case 14. An open map accepts a child key that has no schema entry of its own.
Scenario: a child of an open map is accepted
  Given a cloud ParameterSet sets "<open-map>.<child>"
  And the catalog for "<application-b>" has "<open-map>" with additionalProperties true
  And "<application-a>" does not accept "<open-map>.<child>"
  When the linter checks the environment with that catalog   # NEW STEP NEEDED
  Then the linter report has a PLACE-13 Fix for "<open-map>.<child>" naming "<application-b>"   # NEW STEP NEEDED

# why: case 15. Macro text is a value. A different macro at a nearer level blocks the move.
Scenario: different credential macros at two levels block the move
  Given the cloud ParameterSet sets "<deploy-key>" to a credential macro
  And the namespace ParameterSet sets "<deploy-key>" to a different credential macro
  And only one reached application accepts "<deploy-key>"
  When the linter checks the environment with that catalog   # NEW STEP NEEDED
  Then the linter report has a PLACE-13 Review for the cloud "<deploy-key>"   # NEW STEP NEEDED

# why: case 16. The catalog stores the subchart-local key. An alias prefix is a different key.
Scenario: an umbrella alias prefix does not match a subchart-local catalog key
  Given a cloud ParameterSet sets "<alias>.<deploy-key>"
  And the catalog for "<application-a>" lists "<deploy-key>" and not "<alias>.<deploy-key>"
  And the solution descriptor lists "<application-a>" and "<application-b>"
  And neither catalog lists "<alias>.<deploy-key>"
  When the linter checks the environment with that catalog   # NEW STEP NEEDED
  Then the linter report has a PLACE-13 Review for "<alias>.<deploy-key>"   # NEW STEP NEEDED
  And the review calls it a delete candidate   # NEW STEP NEEDED
```
