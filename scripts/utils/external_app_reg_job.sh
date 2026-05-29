#!/bin/bash

# EXTERNAL JOB - DEPRECATED
base_env_path="$CI_PROJECT_DIR/environments/$1"

if [ -n "$APP_REG_DEFS_JOB" ]; then
    for app_defs_path in "$base_env_path/AppDefs" "$CI_PROJECT_DIR/appdefs"; do
        [ -n "$APP_DEFS_PATH" ] && mkdir -p "$app_defs_path" && cp -rf "$APP_DEFS_PATH"/* "$app_defs_path"
    done

    for reg_defs_path in "$base_env_path/RegDefs" "$CI_PROJECT_DIR/regdefs"; do
        [ -n "$REG_DEFS_PATH" ] && mkdir -p "$reg_defs_path" && cp -rf "$REG_DEFS_PATH"/* "$reg_defs_path"
    done
fi
