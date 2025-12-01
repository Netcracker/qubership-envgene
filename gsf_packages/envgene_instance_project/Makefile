# Makefile for Docker image operations
# Usage: make VERSION=1.0.0

VERSION ?= 1.0.0
SOURCE_IMAGE = ghcr.io/netcracker/qubership-gsf-instance:feature_updating_gsf
TARGET_IMAGE = andyroode/andyroode_gsf:$(VERSION)

.PHONY: pull tag push all

all: pull tag push

pull:
	docker pull $(SOURCE_IMAGE)

tag: pull
	docker tag $(SOURCE_IMAGE) $(TARGET_IMAGE)

push: tag
	docker push $(TARGET_IMAGE)

