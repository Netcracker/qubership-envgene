#########################################
## Stage 1
FROM ghcr.io/netcracker/base-images-module-base:main as base-image

FROM ubuntu:24.04

USER root

RUN mkdir "/etc/ssl"

COPY build_envgene/build/pip.conf /etc/pip.conf
COPY build_envgene/build/requirements.txt /build/requirements.txt
COPY build_envgene/build/requirements.yml /build/requirements.yml
COPY build_envgene/build/sources_ubuntu.list /etc/apt/sources.list
COPY build_envgene/ansible /module/ansible
COPY build_envgene/scripts /module/scripts
COPY python /python

COPY build_* create_* produce_* sort* /build_env/
COPY scripts /build_env/scripts
COPY env-builder /build_env/env-builder
COPY schemas /build_env/schemas

COPY --from=base-image /module /module

ENV ANSIBLE_LIBRARY /module/ansible/library:$ANSIBLE_LIBRARY

RUN apt update -y 
RUN apt remove perl-base -y --allow-remove-essential 
RUN apt autoremove -y 
RUN apt install -y \
    git \
    python3 \
    ca-certificates \
    openssl \
    openssh-client \
    pip \
    coreutils \
    curl \
    sudo \
    zip \
    unzip 
RUN curl --retry 3 --retry-connrefused --retry-delay 5 -LO https://github.com/mozilla/sops/releases/download/v3.9.0/sops-v3.9.0.linux.amd64 
RUN chmod +x sops-v3.9.0.linux.amd64 
RUN mv sops-v3.9.0.linux.amd64 /usr/local/bin/sops 
RUN pip install --no-cache-dir -r /build/requirements.txt 
RUN pip install ansible --upgrade 
RUN rm -rf /usr/local/lib/python3.10/dist-packages/ansible_collections/* 
RUN ansible-galaxy collection install -r /build/requirements.yml -p /module/ansible/collections 
RUN pip install /python/jschon-sort 
RUN pip install /python/envgene 
RUN pip install /python/integration 
RUN chmod 754 /module/scripts/* 
RUN apt autoremove -y 
RUN apt autoclean -y 
RUN apt clean -y 
RUN rm -rf /var/lib/apt/lists/*

WORKDIR /module/ansible
