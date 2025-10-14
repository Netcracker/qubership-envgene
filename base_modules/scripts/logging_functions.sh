#!/usr/bin/env bash

function log_info() {
      echo -e "[\\e[1;94mINFO\\e[0m] $*"
}

function log_warn() {
      echo -e "[\\e[1;93mWARN\\e[0m] $*"
}

function log_error() {
      echo -e "[\\e[1;91mERROR\\e[0m] $*"
}

function fail() {
      log_error "$*"
      exit 1
}
