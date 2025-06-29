# AppDef/RegDef Template Management Test Cases

- [AppDef/RegDef Template Management Test Cases](#appdefregdef-template-management-test-cases)
  - [TC-001-001: Basic AppDef Template Rendering](#tc-001-001-basic-appdef-template-rendering)
  - [TC-001-002: Basic RegDef Template Rendering](#tc-001-002-basic-regdef-template-rendering)
  - [TC-001-003: AppDef Template with Global Overrides](#tc-001-003-appdef-template-with-global-overrides)
  - [TC-001-004: RegDef Template with Global Overrides](#tc-001-004-regdef-template-with-global-overrides)
  - [TC-001-005: AppDef Template with Cluster-Specific Overrides](#tc-001-005-appdef-template-with-cluster-specific-overrides)
  - [TC-001-006: Configuration Override Precedence](#tc-001-006-configuration-override-precedence)
  - [TC-001-007: Using External AppDef/RegDef Files](#tc-001-007-using-external-appdefregdef-files)
  - [TC-001-008: Multiple AppDef Templates](#tc-001-008-multiple-appdef-templates)
  - [TC-001-009: AppDef Template with Environment Variables](#tc-001-009-appdef-template-with-environment-variables)
  - [TC-001-010: Template with Invalid Jinja2 Syntax](#tc-001-010-template-with-invalid-jinja2-syntax)
  - [TC-001-011: AppDef Template with Missing Required Fields](#tc-001-011-appdef-template-with-missing-required-fields)
  - [TC-001-012: RegDef Template with Missing Required Fields](#tc-001-012-regdef-template-with-missing-required-fields)
  - [TC-001-013: Non-Existent External Job](#tc-001-013-non-existent-external-job)
  - [TC-001-014: External Job with Missing Artifact](#tc-001-014-external-job-with-missing-artifact)
  - [TC-001-015: External Job with Invalid Artifact Structure](#tc-001-015-external-job-with-invalid-artifact-structure)

This document describes test cases for the AppDef/RegDef Template Management feature in EnvGene.

## TC-001-001: Basic AppDef Template Rendering

Status: Not Implemented

Pre-requisites:
- EnvGene is installed and configured
- Template directory structure is set up
- A basic AppDef template exists in `/templates/appdefs/`

**Test Steps**:
1. Set `app_reg_def_mode: "local"` in `config.yml`
2. Run the environment build process
3. Examine the generated AppDef file in the environment's AppDefs directory

**Expected Results**:
- The AppDef template is discovered and rendered
- The rendered AppDef file is saved to the environment's AppDefs directory
- The rendered file contains the expected content based on the template

**Notes**:
- This test verifies the basic template discovery and rendering functionality

## TC-001-002: Basic RegDef Template Rendering

**Title**: Verify basic RegDef template rendering functionality

**Prerequisites**:
- EnvGene is installed and configured
- Template directory structure is set up
- A basic RegDef template exists in `/templates/regdefs/`

**Test Steps**:
1. Set `app_reg_def_mode: "local"` in `config.yml`
2. Run the environment build process
3. Examine the generated RegDef file in the environment's RegDefs directory

**Expected Results**:
- The RegDef template is discovered and rendered
- The rendered RegDef file is saved to the environment's RegDefs directory
- The rendered file contains the expected content based on the template

**Notes**:
- This test verifies the basic template discovery and rendering functionality for RegDefs

## TC-001-003: AppDef Template with Global Overrides

**Title**: Verify AppDef template rendering with global configuration overrides

**Prerequisites**:
- EnvGene is installed and configured
- Template directory structure is set up
- A basic AppDef template exists in `/templates/appdefs/`
- Global configuration file exists at `/environments/configuration/appregdef_config.yaml`

**Test Steps**:
1. Set `app_reg_def_mode: "local"` in `config.yml`
2. Configure global overrides in `/environments/configuration/appregdef_config.yaml`:
   ```yaml
   appdefs:
     overrides:
       "com.example:app1":
         version: "2.0.0"
         registry: "custom-registry"
   ```
3. Run the environment build process
4. Examine the generated AppDef file in the environment's AppDefs directory

**Expected Results**:
- The AppDef template is rendered with the global overrides applied
- The rendered file contains the overridden values (version: "2.0.0", registry: "custom-registry")

**Notes**:
- This test verifies that global configuration overrides are correctly applied during template rendering

## TC-001-004: RegDef Template with Global Overrides

**Title**: Verify RegDef template rendering with global configuration overrides

**Prerequisites**:
- EnvGene is installed and configured
- Template directory structure is set up
- A basic RegDef template exists in `/templates/regdefs/`
- Global configuration file exists at `/environments/configuration/appregdef_config.yaml`

**Test Steps**:
1. Set `app_reg_def_mode: "local"` in `config.yml`
2. Configure global overrides in `/environments/configuration/appregdef_config.yaml`:
   ```yaml
   regdefs:
     overrides:
       "docker-registry":
         url: "https://custom-docker-registry.example.com"
   ```
3. Run the environment build process
4. Examine the generated RegDef file in the environment's RegDefs directory

**Expected Results**:
- The RegDef template is rendered with the global overrides applied
- The rendered file contains the overridden values (url: "https://custom-docker-registry.example.com")

**Notes**:
- This test verifies that global configuration overrides are correctly applied during RegDef template rendering

## TC-001-005: AppDef Template with Cluster-Specific Overrides

**Title**: Verify AppDef template rendering with cluster-specific configuration overrides

**Prerequisites**:
- EnvGene is installed and configured
- Template directory structure is set up
- A basic AppDef template exists in `/templates/appdefs/`
- Cluster-specific configuration file exists at `/environments/<cluster-name>/configuration/appregdef_config.yaml`

**Test Steps**:
1. Set `app_reg_def_mode: "local"` in `config.yml`
2. Configure cluster-specific overrides in `/environments/<cluster-name>/configuration/appregdef_config.yaml`:
   ```yaml
   appdefs:
     overrides:
       "com.example:app1":
         version: "3.0.0"
         replicas: 3
   ```
3. Run the environment build process
4. Examine the generated AppDef file in the environment's AppDefs directory

**Expected Results**:
- The AppDef template is rendered with the cluster-specific overrides applied
- The rendered file contains the overridden values (version: "3.0.0", replicas: 3)

**Notes**:
- This test verifies that cluster-specific configuration overrides are correctly applied during template rendering

## TC-001-006: Configuration Override Precedence

**Title**: Verify configuration override precedence (cluster-specific over global)

**Prerequisites**:
- EnvGene is installed and configured
- Template directory structure is set up
- A basic AppDef template exists in `/templates/appdefs/`
- Global configuration file exists at `/environments/configuration/appregdef_config.yaml`
- Cluster-specific configuration file exists at `/environments/<cluster-name>/configuration/appregdef_config.yaml`

**Test Steps**:
1. Set `app_reg_def_mode: "local"` in `config.yml`
2. Configure global overrides in `/environments/configuration/appregdef_config.yaml`:
   ```yaml
   appdefs:
     overrides:
       "com.example:app1":
         version: "2.0.0"
         registry: "global-registry"
   ```
3. Configure cluster-specific overrides in `/environments/<cluster-name>/configuration/appregdef_config.yaml`:
   ```yaml
   appdefs:
     overrides:
       "com.example:app1":
         version: "3.0.0"
   ```
4. Run the environment build process
5. Examine the generated AppDef file in the environment's AppDefs directory

**Expected Results**:
- The AppDef template is rendered with both overrides applied, with cluster-specific taking precedence
- The rendered file contains version: "3.0.0" (from cluster-specific) and registry: "global-registry" (from global)

**Notes**:
- This test verifies the correct precedence order of configuration overrides

## TC-001-007: Using External AppDef/RegDef Files

**Title**: Verify using external AppDef/RegDef files from job artifacts

**Prerequisites**:
- EnvGene is installed and configured
- A job exists that produces a `definitions.zip` file containing AppDef and RegDef files
- The job artifact is accessible

**Test Steps**:
1. Set `APP_REG_DEFS_JOB: "appdef-generation-job"` in the pipeline configuration
2. Set `app_defs_path: "AppDefs"` and `reg_defs_path: "RegDefs"` in the pipeline configuration
3. Run the environment build process
4. Examine the AppDefs and RegDefs directories in the environment

**Expected Results**:
- The `definitions.zip` file is downloaded and unpacked
- AppDef files are copied from the `AppDefs` directory in the artifact to the environment's AppDefs directory
- RegDef files are copied from the `RegDefs` directory in the artifact to the environment's RegDefs directory
- No local template rendering occurs

**Notes**:
- This test verifies the functionality of using external AppDef/RegDef files instead of rendering templates locally

## TC-001-008: Multiple AppDef Templates

**Title**: Verify rendering of multiple AppDef templates

**Prerequisites**:
- EnvGene is installed and configured
- Template directory structure is set up
- Multiple AppDef templates exist in `/templates/appdefs/`

**Test Steps**:
1. Set `app_reg_def_mode: "local"` in `config.yml`
2. Run the environment build process
3. Examine the generated AppDef files in the environment's AppDefs directory

**Expected Results**:
- All AppDef templates are discovered and rendered
- Each rendered AppDef file is saved to the environment's AppDefs directory with the correct name
- Each rendered file contains the expected content based on its template

**Notes**:
- This test verifies the ability to handle multiple templates simultaneously

## TC-001-009: AppDef Template with Environment Variables

**Title**: Verify AppDef template rendering with environment variables

**Prerequisites**:
- EnvGene is installed and configured
- Template directory structure is set up
- An AppDef template exists in `/templates/appdefs/` that uses environment variables

**Test Steps**:
1. Set `app_reg_def_mode: "local"` in `config.yml`
2. Set environment variables that are referenced in the template
3. Run the environment build process
4. Examine the generated AppDef file in the environment's AppDefs directory

**Expected Results**:
- The AppDef template is rendered with the environment variables correctly substituted
- The rendered file contains the values from the environment variables

**Notes**:
- This test verifies that environment variables are correctly accessible within templates

## TC-001-010: Template with Invalid Jinja2 Syntax

**Title**: Verify error handling for templates with invalid Jinja2 syntax

**Prerequisites**:
- EnvGene is installed and configured
- Template directory structure is set up
- An AppDef template exists in `/templates/appdefs/` with invalid Jinja2 syntax

**Test Steps**:
1. Set `app_reg_def_mode: "local"` in `config.yml`
2. Run the environment build process
3. Examine the build logs and error messages

**Expected Results**:
- The build process detects the invalid Jinja2 syntax
- An appropriate error message is displayed indicating the syntax error
- The build process fails gracefully

**Notes**:
- This test verifies error handling for invalid template syntax

## TC-001-011: AppDef Template with Missing Required Fields

**Title**: Verify validation of required fields in AppDef templates

**Prerequisites**:
- EnvGene is installed and configured
- Template directory structure is set up
- An AppDef template exists in `/templates/appdefs/` that is missing required fields (e.g., name, artifactId)

**Test Steps**:
1. Set `app_reg_def_mode: "local"` in `config.yml`
2. Run the environment build process
3. Examine the build logs and error messages

**Expected Results**:
- The build process detects the missing required fields
- An appropriate error message is displayed indicating which fields are missing
- The build process fails gracefully

**Notes**:
- This test verifies validation of required fields in AppDef templates

## TC-001-012: RegDef Template with Missing Required Fields

**Title**: Verify validation of required fields in RegDef templates

**Prerequisites**:
- EnvGene is installed and configured
- Template directory structure is set up
- A RegDef template exists in `/templates/regdefs/` that is missing required fields (e.g., name, type)

**Test Steps**:
1. Set `app_reg_def_mode: "local"` in `config.yml`
2. Run the environment build process
3. Examine the build logs and error messages

**Expected Results**:
- The build process detects the missing required fields
- An appropriate error message is displayed indicating which fields are missing
- The build process fails gracefully

**Notes**:
- This test verifies validation of required fields in RegDef templates

## TC-001-013: Non-Existent External Job

**Title**: Verify error handling for non-existent external job

**Prerequisites**:
- EnvGene is installed and configured

**Test Steps**:
1. Set `APP_REG_DEFS_JOB: "non-existent-job"` in the pipeline configuration
2. Run the environment build process
3. Examine the build logs and error messages

**Expected Results**:
- The build process detects that the specified job does not exist
- An appropriate error message is displayed
- The build process fails gracefully

**Notes**:
- This test verifies error handling for non-existent external jobs

## TC-001-014: External Job with Missing Artifact

**Title**: Verify error handling for external job with missing artifact

**Prerequisites**:
- EnvGene is installed and configured
- A job exists but does not produce a `definitions.zip` file

**Test Steps**:
1. Set `APP_REG_DEFS_JOB: "job-without-artifact"` in the pipeline configuration
2. Run the environment build process
3. Examine the build logs and error messages

**Expected Results**:
- The build process detects that the required artifact is missing
- An appropriate error message is displayed
- The build process fails gracefully

**Notes**:
- This test verifies error handling for external jobs with missing artifacts

## TC-001-015: External Job with Invalid Artifact Structure

**Title**: Verify error handling for external job with invalid artifact structure

**Prerequisites**:
- EnvGene is installed and configured
- A job exists that produces a `definitions.zip` file with an invalid structure

**Test Steps**:
1. Set `APP_REG_DEFS_JOB: "job-with-invalid-artifact"` in the pipeline configuration
2. Set `app_defs_path: "NonExistentPath"` in the pipeline configuration
3. Run the environment build process
4. Examine the build logs and error messages

**Expected Results**:
- The build process detects that the specified path in the artifact does not exist
- An appropriate error message is displayed
- The build process fails gracefully

**Notes**:
- This test verifies error handling for external jobs with invalid artifact structure
