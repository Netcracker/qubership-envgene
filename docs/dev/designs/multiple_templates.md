# Ability to set separate versions of templates for BG domain parts

## Problem statement

EnvGene needs to be able to use different template artifacts for rendering BGD
namespaces: common, peer, origin.

## Proposed solutions

### A

Render all 3 templates and replace bgd namespaces in common template with
namespaces from 2 templates

### B

Render template/environment descriptors for all template artifact.

bg_domain object is now rendered before namespaces.

During namespaces rendering check bg_domain and if namespace is origin or peer,
use namespace template and template_override value from respective template/environment descriptor.

During processing paramsets check namespace role and use paramsets from respective
templates.
