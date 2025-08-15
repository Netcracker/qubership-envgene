#!/bin/bash
set -e

artifact_name="test_template"
build_name=${artifact_name}".zip"
git_location=$(git symbolic-ref -q --short HEAD || git describe --tags --exact-match)
version_file=version.txt

add_git_version() {
    local git_tag_branch=$1
    local file=$2
    if git tag --list |grep -q -e "^$git_tag_branch$"; then
      git_line=tags/$git_tag_branch
    elif git branch -r |grep -q -e "origin/$git_tag_branch$"; then
      git_line=origin/$git_tag_branch
    else
      git_line=$git_tag_branch
    fi
    git show --format=format:'date:          %ci
commit hash:   %H
branch or tag: %d%n' -s "$git_line" >> "$file"
}

# Add version file
add_git_version "$git_location" "$version_file"

rm -f "$build_name"

mkdir -p ./target

echo "Create repo archive"

zip  "./target/${build_name}" "./"${artifact_name}.yml

echo "Archive has been created"

# restore
rm -f $version_file

echo "done."
