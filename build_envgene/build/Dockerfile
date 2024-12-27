#########################################
## Stage 1
FROM ghcr.io/netcracker/base-images-module-base:main as base-image

FROM ubuntu:24.04

USER root

# Создаем необходимые директории
RUN mkdir "/etc/ssl"

# Копируем файлы в контейнер
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

# Устанавливаем переменные окружения
ENV ANSIBLE_LIBRARY /module/ansible/library:$ANSIBLE_LIBRARY

# Устанавливаем зависимости
RUN apt update -y \
    && apt remove perl-base -y --allow-remove-essential \
    && apt autoremove -y \
    && apt install -y \
        git \
        python3-full \
        python3-pip \
        python3-venv \
        libxml2-dev \
        libxslt-dev \
        zlib1g-dev \
        build-essential \
        ca-certificates \
        openssl \
        openssh-client \
        coreutils \
        curl \
        sudo \
        zip \
        unzip \
    && curl --retry 3 --retry-connrefused --retry-delay 5 -LO https://github.com/mozilla/sops/releases/download/v3.9.0/sops-v3.9.0.linux.amd64 \
    && chmod +x sops-v3.9.0.linux.amd64 \
    && mv sops-v3.9.0.linux.amd64 /usr/local/bin/sops

# Обновляем pip с использованием флага --break-system-packages
RUN python3 -m ensurepip --upgrade \
    && python3 -m pip install --upgrade pip --break-system-packages

# Устанавливаем Python-зависимости
RUN pip install --no-cache-dir lxml==4.9.3 \
    && pip install --no-cache-dir -r /build/requirements.txt \
    && pip install ansible --upgrade \
    && rm -rf /usr/local/lib/python3.10/dist-packages/ansible_collections/* \
    && ansible-galaxy collection install -r /build/requirements.yml -p /module/ansible/collections \
    && pip install /python/jschon-sort \
    && pip install /python/envgene \
    && pip install /python/integration

# Настраиваем права на скрипты и очищаем временные файлы
RUN chmod 754 /module/scripts/* \
    && apt autoremove -y \
    && apt autoclean -y \
    && apt clean -y \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /module/ansible
