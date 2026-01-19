# Ability to set separate versions of templates for BG domain parts

## Problem statement

EnvGene needs to be able to use different template artifacts for rendering BGD
namespaces: common, peer, origin.

## Proposed solutions

### A

Render all 3 templates and replace bgd namespaces in common template with
namespaces from 2 templates

**Cons:**

- Spends time rendering unnecessary files

### B

Move paramsets, namespace templates and merge namespaces(bgd namespaces) part of
template descriptor(because of template overrides) from bgd template into common
template while adding `-peer` and `-origin` postfixes to files. And editing
contents of those files like paramsets and etc by adding `-peer` and `-origin`
postixes there as well (During env template processing)

**Cons:**

- We need to add requirement that user has to specify which namespaces are peer
  and origin in template descriptor

### C

Same as approach A, but instead of rendering everything render only namespaces
for bgd templates

**Cons:**

- Not sure if we can do this
- Feels like it's gonna take lot of time to implement
