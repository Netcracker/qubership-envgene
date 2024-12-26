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
RUN pip install --no-cache-dir lxml==4.9.3 ruamel.yaml==0.18.5 ruamel.yaml.clib==0.2.8 ruyaml==0.91.0
RUN pip install --no-cache-dir jschon==0.11.0 jsonschema==4.19.1 diagrams==0.23.3 jmespath==1.0.1
RUN pip install --no-cache-dir semantic-version==2.10.0 termcolor==2.4.0 ansible-core==2.13.3
RUN pip install --no-cache-dir ansible-base==2.10.17 ansible_runner==2.3.5 hiyapyco==0.6.0
RUN pip install --no-cache-dir cffi==1.16.0 click==8.1.3

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
