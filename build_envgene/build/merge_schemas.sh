#!/bin/sh
set -eu

source_dir=$1
target_dir=$2

mkdir -p "$target_dir"
find "$source_dir" -type f | while IFS= read -r schema_file; do
    relative_path="${schema_file#"$source_dir"/}"
    destination="$target_dir/$relative_path"
    mkdir -p "$(dirname "$destination")"
    if [ ! -e "$destination" ]; then
        cp "$schema_file" "$destination"
    fi
done