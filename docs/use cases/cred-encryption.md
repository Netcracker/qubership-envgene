
# Credential Encryption Use Cases

- [Credential Encryption Use Cases](#credential-encryption-use-cases)
  - [Description](#description)
  - [Roles](#roles)
    - [1. Preparing the Configurator's local machine](#1-preparing-the-configurators-local-machine)
    - [2. Enabling SOPS Encryption in Repository](#2-enabling-sops-encryption-in-repository)
    - [3. Adding New Sensitive Parameter](#3-adding-new-sensitive-parameter)
    - [4. Modifying the value of a sensitive parameter](#4-modifying-the-value-of-a-sensitive-parameter)
    - [5. Migrating from Fernet to SOPS](#5-migrating-from-fernet-to-sops)
    - [6. Encryption key rotation](#6-encryption-key-rotation)

## Description

Описанные ниже из кейсы относятся в функционалу [Credential Encryption](/docs/features/cred-encryption.md)

## Roles

EnvGene Admin
EnvGene Configurator
e2e Admin

### 1. Preparing the Configurator's local machine

**Description:**

**Prerequisites**:

**Process**:

**Result**:

### 2. Enabling SOPS Encryption in Repository

**Description:** Описывает включения кред энкрипта в сопс бэкенде в энвген репозитории. Энкрипт должен включаться синхронно с другими системами которые интегрируются с энвгеном, например с потребителями эффектив сета

**Prerequisites**:

- Repository admin access
- Пре коммит хук настроен в локальном репозитории Админа в соответствии с [Preparing the Configurator's local machine](#1-preparing-the-configurators-local-machine)

**Process**:

1. Envgene Admin генерирует age пару
2. Envgene Админ передает публичный ключ из пары e2e админу
3. e2e админ создает общий публичный ключ как сумму публичных ключей всех систем участвующий в управлении сенсетив параметры (те системы которые энкриптят и декриптят)
4. e2e админ передает энвген админу общий публичный ключ (PUBLIC_AGE_KEYS)
5. Энвген админ задает CICD переменные репозитория
   1. [PUBLIC_AGE_KEYS](/docs/instance-pipeline-parameters.md#public_age_keys)
   2. [ENVGENE_AGE_PRIVATE_KEY](/docs/instance-pipeline-parameters.md#envgene_age_private_key)
6. Энвген админ включает для репозитория [GitLab Server-side Git Hooks](/docs/features/cred-encryption.md#gitlab-server-side-git-hooks) GAP
7. Admin updates `config.yml`:

   ```yaml
   crypt: true
   crypt_backend: "SOPS"
   ```

8. Админ коммитит локально
9. Прекоммит хук энкриптит креды в репозитории, создавая шейд файлы
10. Админ пушит времоут репо
11. Серверный хук валидирует изменение
12. Серверный хук принимает коммит

**Result**:

- All credentials in the repo are encrypted
- Последующие 

### 3. Adding New Sensitive Parameter

**Description:** TBD

**Prerequisites**:

- Encryption enabled
- настроен сопс бэкенд
- настроены шейд режим
- Local hook installed

**Process**:

1. Configurator adds sensitive parameter via cred macro
2. Configurator generates Env Instance
3. Envgene generates shades креды
4. Configurator задает значение сенсетив параметра в шейд креде
5. Configurator коммитит локально
6. Pre-commit hook auto-encrypts value
7. Админ пушит времоут репо
8. Серверный хук валидирует изменение
9. Серверный хук принимает коммит

**Result**:

- TBD

### 4. Modifying the value of a sensitive parameter

**Description:** TBD

**Prerequisites**:

- Encryption enabled
- настроен сопс бэкенд
- настроены шейд режим
- Local hook installed

**Process**:

1. Configurator задает значение сенсетив параметра в кред файле вместо value valueisset
2. Configurator коммитит локально
3. Pre-commit hook обновляет значение шэйд креда
4. Админ пушит времоут репо
5. Серверный хук валидирует изменение
6. Серверный хук принимает коммит

**Result**:

- TBD

---

### 5. Migrating from Fernet to SOPS

**Description:** TBD

**Prerequisites**:

- Fernet backend configured
- все креды репозитория заинкрипчены сопсом
- фернет ключ задан в варах репозитория
- Local hook installed

**Process**:

1. Админ запуском декрипт скрипта декриптит все креды в репозитории
2. Admin changes backend in `config.yml`

   ```yaml
   crypt_backend: "SOPS"
   ```

3. Admin коммитит локально
4. Прекоммит хук энкриптит креды в репозитории, создавая шейд файлы
5. Админ пушит времоут репо
6. Серверный хук валидирует изменение
7. Серверный хук принимает коммит

**Result**:

- Все креды репозитория заинкрипчены

### 6. Encryption key rotation

**Description:**

**Prerequisites**:

**Process**:

**Result**:
