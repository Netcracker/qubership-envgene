# catalog-overall

## env-build-instance


pos-run-envgene-build-instance-with-build-instance
pos-run-envgene-build-instance-with-cloud-passport.yaml
pos-run-envgene-build-instance-with-effective-set-and-single-sd-data.yaml
pos-run-envgene-build-instance-with-effective-set.yaml
pos-run-envgene-build-instance-with-import-to-cmdb.yaml
pos-run-envgene-build-instance-with-inventory-init-and-multiple-sd.yaml
pos-run-envgene-build-instance-with-inventory-init-and-single-sd-data.yaml
pos-run-envgene-build-instance-with-sd-delta-and-sd-merge.yaml

## cred-rotation 
pos-run-envgene-cred-rotation-cred-rotation-app.yaml
pos-run-envgene-cred-rotation-with-cred-rotation-namespace.yaml
pos-run-envgene-cred-rotation-with-multiple-cred-rotation-multiple-app-multiple-context.yaml
pos-run-envgene-cred-rotation-with-multiple-cred-rotation-multiple-app-single-context.yaml

# envgen test-cases

## red-rotation 
- empty

## AppDef/RegDef Template Management Test Cases
TC-001-001: Basic AppDef Template Rendering
TC-001-002: Basic RegDef Template Rendering
TC-001-003: AppDef Template with Global Overrides
TC-001-004: RegDef Template with Global Overrides
TC-001-005: AppDef Template with Cluster-Specific Overrides
TC-001-006: Configuration Override Precedence
TC-001-007: Using External AppDef/RegDef Files
TC-001-008: Multiple AppDef Templates
TC-001-009: AppDef Template with Environment Variables
TC-001-010: Template with Invalid Jinja2 Syn
TC-001-011: AppDef Template with Missing Required Fields
TC-001-012: RegDef Template with Missing Required Fields
TC-001-013: Non-Existent External Job
TC-001-014: External Job with Missing Artifact
TC-001-015: External Job with Invalid Artifact Structure


## 1) catalog-overall

### 1.1 env-build-instance

| Module | Feature | Coverage Type | ID / File | What it validates (key intent) |
|---|---|---|---|---|
| catalog-overall | env-build-instance | AUTO | `pos-run-envgene-build-instance-with-build-instance.yaml` |  |
| catalog-overall | env-build-instance | AUTO | `pos-run-envgene-build-instance-with-cloud-passport.yaml` |  |
| catalog-overall | env-build-instance | AUTO | `pos-run-envgene-build-instance-with-effective-set.yaml` |  |
| catalog-overall | env-build-instance | AUTO | `pos-run-envgene-build-instance-with-effective-set-and-single-sd-data.yaml` |  |
| catalog-overall | env-build-instance | AUTO | `pos-run-envgene-build-instance-with-import-to-cmdb.yaml` |  |
| catalog-overall | env-build-instance | AUTO | `pos-run-envgene-build-instance-with-inventory-init-and-multiple-sd.yaml` |  |
| catalog-overall | env-build-instance | AUTO | `pos-run-envgene-build-instance-with-inventory-init-and-single-sd-data.yaml` |  |
| catalog-overall | env-build-instance | AUTO | `pos-run-envgene-build-instance-with-sd-delta-and-sd-merge.yaml` |  |

### 1.2 cred-rotation

| Module | Feature | Coverage Type | ID / File | What it validates (key intent) |
|---|---|---|---|---|
| catalog-overall | cred-rotation | AUTO | `pos-run-envgene-cred-rotation-cred-rotation-app.yaml` |  |
| catalog-overall | cred-rotation | AUTO | `pos-run-envgene-cred-rotation-with-cred-rotation-namespace.yaml` |  |
| catalog-overall | cred-rotation | AUTO | `pos-run-envgene-cred-rotation-with-multiple-cred-rotation-multiple-app-multiple-context.yaml` |  |
| catalog-overall | cred-rotation | AUTO | `pos-run-envgene-cred-rotation-with-multiple-cred-rotation-multiple-app-single-context.yaml` |  |

---

## 2) Documented Test Cases (TC) — coverage in docs

### 2.1 AppDef/RegDef Template Management (TC-001-*)

| Module | Feature | Coverage Type | TC IDs | Coverage focus |
|---|---|---|---|---|
| templates | AppDef/RegDef Template Management | TC | TC-001-001…TC-001-002 |  |
| templates | AppDef/RegDef Template Management | TC | TC-001-003…TC-001-006 |  |
| templates | AppDef/RegDef Template Management | TC | TC-001-007 | |
| templates | AppDef/RegDef Template Management | TC | TC-001-008…TC-001-009 |  |
| templates | AppDef/RegDef Template Management | TC | TC-001-010…TC-001-012 | |
| templates | AppDef/RegDef Template Management | TC | TC-001-013…TC-001-015 |  |

### 2.2 Credential Files Encryption via Git pre-commit hook (TC-004-*)

| Module | Feature | Coverage Type | TC IDs | Coverage focus |
|---|---|---|---|---|
| security | Credential files encryption (git hook) | TC | TC-004-001 |  |
| security | Credential files encryption (git hook) | TC | TC-004-002 |  |
| security | Credential files encryption (git hook) | TC | TC-004-003…TC-004-005 |  |
| security | Credential files encryption (git hook) | TC | TC-004-006…TC-004-008 |  |

### 2.3 Cluster Endpoint Information in Topology Context (TC-CETC-*)

| Module | Feature | Coverage Type | TC IDs | Coverage focus |
|---|---|---|---|---|
| calculator/topology | Cluster endpoint info in topology context | TC | TC-CETC-001 | |
| calculator/topology | Cluster endpoint info in topology context | TC | TC-CETC-002…TC-CETC-005 | |
| calculator/topology | Cluster endpoint info in topology context | TC | TC-CETC-006 | ` |
| calculator/topology | Cluster endpoint info in topology context | TC | TC-CETC-007 |  |

### 2.4 Automatic Environment Name Derivation (TC-003-*)

| Module | Feature | Coverage Type | TC IDs | Coverage focus |
|---|---|---|---|---|
| inventory | Automatic environment name derivation | TC | TC-003-001…TC-003-003 | Use explicit `inventory.environmentName` or derive from folder name |
| inventory | Automatic environment name derivation | TC | TC-003-004 | Invalid structure → proper error about unable to derive name |
| inventory | Automatic environment name derivation | TC | TC-003-005 | Template rendering uses derived `current_env.name` correctly |

---

## 3) Use Cases (UC) — specs that should be converted into TCs / automated runs

### 3.1 Environment Instance Generation (EIG)

| Module | Feature | Coverage Type | UC IDs | Coverage focus |
|---|---|---|---|---|
| env-instance-generation | Namespace folder name generation | UC | UC-EIG-NF-1…UC-EIG-NF-8 | Namespace folder naming rules: non-BG vs BG roles + deploy_postfix |
| env-instance-generation | Template artifacts selection | UC | UC-EIG-TA-1…UC-EIG-TA-3 | Artifact selection: `artifact` vs `bgNsArtifacts` with/without BG Domain |

### 3.2 Environment Template Downloading

| Module | Feature | Coverage Type | UC IDs | Coverage focus |
|---|---|---|---|---|
| template-downloading | Template artifact downloading | UC | UC-1-1…UC-2-4 | Matrix: GAV/app:ver × Specific/SNAPSHOT × ZIP/DU × registry scope |

### 3.3 Calculator CLI (Effective Set v2.0)

| Module | Feature | Coverage Type | UC IDs | Coverage focus |
|---|---|---|---|---|
| calculator-cli | deployPostfix matching logic | UC | UC-CC-DP-1…UC-CC-DP-4 | Exact match / BG match / errors when no match found |
| calculator-cli | Macro resolution type preservation | UC | UC-CC-MR-1…UC-CC-MR-2 | Preserve types + preserve complex structures/literal blocks |
| calculator-cli | Cross-level parameter references | UC | UC-CC-HR-1…UC-CC-HR-6 | Allowed: lower→higher; Forbidden: higher→lower |
| calculator-cli | Cross-context parameter references | UC | UC-CC-CR-1…UC-CC-CR-6 | Forbidden references between deploy/e2e/tech contexts |

### 3.4 Blue-Green Deployment (bg_manage)

| Module | Feature | Coverage Type | UC IDs | Coverage focus |
|---|---|---|---|---|
| blue-green | BG manage operations | UC | UC-BG-1…UC-BG-9 | Init/Warmup/Promote/Commit/Rollback + reverse operations; state files transitions |

---
