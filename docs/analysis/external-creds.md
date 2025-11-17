# External Creds

- [External Creds](#external-creds)
  - [Problem Statement](#problem-statement)
  - [Open Question](#open-question)
    - [Internal](#internal)
    - [External](#external)
  - [Limitation](#limitation)
  - [Assumption](#assumption)
  - [Proposed Approach](#proposed-approach)
    - [Option 1. Without Credential in EnvGene](#option-1-without-credential-in-envgene)
      - [\[Option 1\] Cred Snippet](#option-1-cred-snippet)
      - [\[Option 1\] Parameter in Effective Set](#option-1-parameter-in-effective-set)
    - [Option 2. With Credential in EnvGene](#option-2-with-credential-in-envgene)
      - [\[Option 2\] Cred Snippet](#option-2-cred-snippet)
      - [\[Option 2\] Credential Template](#option-2-credential-template)
      - [\[Option 2\] Credential](#option-2-credential)
      - [\[Option 2\] Parameter in Effective Set](#option-2-parameter-in-effective-set)
    - [Option 1 vs Option 2](#option-1-vs-option-2)
    - [`ExternalSecret` CR](#externalsecret-cr)
    - [KV Store Structure](#kv-store-structure)
    - [Secret Store](#secret-store)
    - [EnvGene System Creds](#envgene-system-creds)
    - [Transformer](#transformer)
    - [Migration](#migration)
    - [Use Cases](#use-cases)

## Problem Statement

В данный момент EnvGene не умеет управлять кредами, значения которых заданы в экстернал кред сторе

## Open Question

### Internal

- [ ] Что делать с аттрибутами `defaultCredentialsId`, `maasConfig.credentialsId` Cloud и Namespace? Оставить как есть или задавать через Cred snippet
- [ ] Допустим ли тот факт, что переход на Ext Store потребует изменений в темплейтах?
- [+] Должен быть отдельно `creds.link` и `creds.create`
  - Да
- [+] Копируем креды в эффектив сет фолдер? Указываем линку на файл с кредами энва в каком то параметре (вводим метадата файл, еще и версию туда положим)?
  - Не копируется и не указывается линк. Энвген сгенернет сниппет достаточный для генерации ExternalSecret CR
- [ ] В темплейте и эффектив сете один и тот же сниппет?
- [ ] Option 1 или Option 2?
- [ ] Какие нужны валидации?
  - `creds.link() указывающий на локал`
  - `creds.get() указывающий на ремоут`
  - `creds.create()` когада создано

### External

- [+] `remoteRef.key` это про изоляцию?
   1. Да. Это иерархический способ хранения, на основе которого можно построить политики доступа
- [ ] Где происходит трансформация эффектив сета:
   1. в xxxProvider -> в либах (которые используются EnvGene и пайпами)
   2. в Argo Vault Plugin -> ???
   3. в External Secrtes Operator -> в Helm либе
- [ ] Что насчет того что бы использовать как сепаратор `/` в энвгене, но трансформеры/скрипт создания приведет этот реф к нормализованому формату
- [ ] Подерживает ли Azure `<json-path>`
- [ ] Какие ограничения на имя креда?
- [ ] Какая структура хранения Creds для non-cloud систем?

## Limitation

1. Один секрет на путь KV store

## Assumption

1. Трансформаторы нормализуют `remoteRef`, т.е.:
   1. Приводит к виду `0-9`, `a-z`, `A-Z`, `-`
   2. Обеспечивает 127 Char Limit
2. Имя кластера и Cloud совпадают
3. Cred должен создаваться `creds.create()` до его использования `creds.link()`
4. При переходе на External Cred Store необходимо изменение EnvGene template
5. Уникальность Cred определяется как `<cred-id>` + `<secret-store>` + `<remote-ref-key>`

## Proposed Approach

![external-cred](/docs/images/external-cred.png)
![external-cred-transformation](/docs/images/external-cred-transformation.png)

### Option 1. Without Credential in EnvGene

#### [Option 1] Cred Snippet

В дополнение к уже существующему snippet `creds.get()` для локальных Cred, для интеграции с External Cred Store вводятся два новых snippet:

- `creds.create()`: Для идемпотентного создания Cred в Ext Cred Store и связывания его с параметром
- `creds.link()`: Для связывания параметра с созданным ранее (существующим) Cred в Ext Cred Store

`creds.get()` по-прежнему полностью поддерживается для работы с локальными Cred.

```yaml
# AS IS Cred snippet
<parameter-key>: "${creds.get('<cred-id>').secret|username|password}"

# TO BE Cred snippet
<parameter-key>: "${creds.get|link|create('<cred-id>', secretStore: '<secret-store>', remoteRefKey: '<remote-ref-key>', argoResolve: true|false).<json-path>}"

# Example
global.secrets.streamingPlatform.password: "${creds.create('cdc-streaming-cred', remoteRefKey: {{ current_env.cloud }}/{{ current_env.name }}/{{ current_env.name }}-bss ).password}"
global.secrets.streamingPlatform.username: "${creds.create('cdc-streaming-cred', remoteRefKey: {{ current_env.cloud }}/{{ current_env.name }}/{{ current_env.name }}-bss ).username}"
TOKEN: "${creds.link('app-cred', secretStore: custom-store, remoteRefKey: very/special/path, argoResolve: false)}"
```

1. Cred snippet задается в значение параметра в:
   1. EnvGene template
   2. Environment specific parameter set
2. Cred snippet содержит:
   1. Обязательный аттрибут `<cred-id>`
   2. Опциональный аттрибут `secretStore`
      1. Значение по умолчанию - `default-store`
   3. Опциональный аттрибут `remoteRefKey`
      1. В качестве сепаратора уровней иерархической структуры хранения используется `/`
      2. Лидирующий `/` не задается
      3. Значение по умолчанию, зависит от EnvGene объекта на котором задан Cred через `creds.create()`:
         1. Tenant, Cloud -> `<cloud-name>`
         2. Namespace -> `<cloud-name>/<env-name>/<namespace-name>`
         3. Application -> `<cloud-name>/<env-name>/<namespace-name>/<application-name>`
      4. При использование `creds.link()` значение по умолчанию - `<cloud-name>`
   4. Опциональный аттрибут `<json-path>`, который определяет JSON path в значение Cred
   5. Опциональный аттрибут `argoResolve: true|false`, который определяет, кто будет обрабатывать данный snippet в деплоймент контекст. Обрабатывается Argo компонентами.
3. Cred snippet позволяет использовать EnvGene макросы для параметризации:

    ```yaml
    # Бизнес солюшен -> Платформа
    ## Параметры платформенного солюшена
    DBAAS_CLUSTER_DBA_CREDENTIALS_USERNAME: ${creds.create('dbaas-creds', remoteRefKey: {{ current_env.cloud }}).username} # remoteRefKey: ocp-05
    DBAAS_CLUSTER_DBA_CREDENTIALS_PASSWORD: ${creds.create('dbaas-creds', remoteRefKey: {{ current_env.cloud }}).password} # remoteRefKey: ocp-05
    ## Параметры Клауд Паспорта для бизнес солюшена
    DBAAS_CLUSTER_DBA_CREDENTIALS_USERNAME: ${creds.link('dbaas-creds', remoteRefKey: ocp-05).username}
    DBAAS_CLUSTER_DBA_CREDENTIALS_PASSWORD: ${creds.link('dbaas-creds', remoteRefKey: ocp-05).password}
    ```

    ```yaml
    # Приложение А -> Non cloud service
    ## Когда remoteRefKey задается через additionalTemplateVariables
    QMS_AUTH_CLIENT_ID: "${creds.link('ID_AUTH_CLIENT_CREDS', remoteRefKey: {{ current_env.additionalTemplateVariables.qms-cred-ref }}).id}"
    QMS_AUTH_CLIENT_SECRET: "${creds.link('ID_AUTH_CLIENT_CREDS', remoteRefKey: {{ current_env.additionalTemplateVariables.qms-cred-ref }}).secret}"
    ## Когда remoteRefKey задается в Энвген креде
    QMS_AUTH_CLIENT_ID: "${creds.link('ID_AUTH_CLIENT_CREDS', remoteRefKey: envgeneNullValue).id}"
    QMS_AUTH_CLIENT_SECRET: "${creds.link('ID_AUTH_CLIENT_CREDS', remoteRefKey: envgeneNullValue).secret}"
    ```

    ```yaml
    # Приложение А -> Приложение B в одном/разных нс, одного энва
    ## Опция 1
    ### Параметры приложения предоставляющее сервис
    QIP_BILL_CREDIT_PASSWORD: "${creds.create('ID_QIP_BILL_CREDIT_CREDS', remoteRefKey: {{ current_env.cloud }}/{{ current_env.name }}/{{ current_env.name }}-bss).password}" # ocp-05/env-1/env-1-bss
    QIP_BILL_CREDIT_USERNAME: "${creds.create('ID_QIP_BILL_CREDIT_CREDS', remoteRefKey: {{ current_env.cloud }}/{{ current_env.name }}/{{ current_env.name }}-bss).username}" # ocp-05/env-1/env-1-bss
    ### Параметры приложения потребляющего сервис
    APPLY_BILL_CREDIT_AUTH_PASSWORD: "${creds.link('ID_QIP_BILL_CREDIT_CREDS', remoteRefKey: {{ current_env.cloud }}/{{ current_env.name }}/{{ current_env.name }}-bss).password}" # ocp-05/env-1/env-1-bss
    APPLY_BILL_CREDIT_AUTH_USERNAME: "${creds.link('ID_QIP_BILL_CREDIT_CREDS', remoteRefKey: {{ current_env.cloud }}/{{ current_env.name }}/{{ current_env.name }}-bss).username}" # ocp-05/env-1/env-1-bss
    ## Опция 2 (Возможно только в отдельных кейсах(в каких?) )
    ### Параметры приложения предоставляющее сервис
    QIP_BILL_CREDIT_PASSWORD: "${creds.create('ID_QIP_BILL_CREDIT_CREDS', remoteRefKey: {{ current_env.cloud }}/{{ current_env.name }}/{{ current_env.name }}-bss).password}" # ocp-05/env-1/env-1-bss
    QIP_BILL_CREDIT_USERNAME: "${creds.create('ID_QIP_BILL_CREDIT_CREDS', remoteRefKey: {{ current_env.cloud }}/{{ current_env.name }}/{{ current_env.name }}-bss).username}" # ocp-05/env-1/env-1-bss
    ### Параметры приложения потребляющего сервис
    APPLY_BILL_CREDIT_AUTH_PASSWORD: "${QIP_BILL_CREDIT_PASSWORD}"
    APPLY_BILL_CREDIT_AUTH_USERNAME: "${QIP_BILL_CREDIT_USERNAME}"
    ## Опция 3 (Возможно только в отдельных кейсах(в каких? )
    ### Общие параметры для приложения предоставляющего и потребляющего сервис
    QIP_BILL_CREDIT_PASSWORD: "${creds.create('ID_QIP_BILL_CREDIT_CREDS', remoteRefKey: {{ current_env.cloud }}/{{ current_env.name }}/{{ current_env.name }}-bss).password}" # ocp-05/env-1/env-1-bss
    QIP_BILL_CREDIT_USERNAME: "${creds.create('ID_QIP_BILL_CREDIT_CREDS', remoteRefKey: {{ current_env.cloud }}/{{ current_env.name }}/{{ current_env.name }}-bss).username}" # ocp-05/env-1/env-1-bss
    ```

    ```yaml
    # Приложение А -> Приложение B в разных энвах одного кластера
    ## Параметры приложения предоставляющее сервис
    ## Опция 1
    PIM_TOKEN: "${creds.create('PIM_TOKEN').password}" # ocp-05/design-time/design-time/CloudBSS-PIM
    ## Параметры приложения потребляющего сервис
    DESIGN_TIME_PIM_TOKEN: "${creds.link('PIM_TOKEN', remoteRefKey: {{ current_env.cloud }}/design-time/design-time/CloudBSS-PIM).password}" # ocp-05/design-time/design-time/CloudBSS-PIM
    ## Опция 2
    PIM_TOKEN: "${creds.create('PIM_TOKEN', remoteRefKey: {{ current_env.cloud }}/{{ current_env.name }}).password}" # ocp-05/design-time
    ## Параметры приложения потребляющего сервис
    DESIGN_TIME_PIM_TOKEN: "${creds.link('PIM_TOKEN', remoteRefKey: {{ current_env.cloud }}/design-time).password}" # ocp-05/design-time
    ```

    ```yaml
    # Приложение А -> Приложение B в разных кластерах
    ## Параметры приложения предоставляющее сервис
    QTP_TOKEN: "${creds.create('QTP_TOKEN').password}" # ocp-05/env-1
    ## Параметры приложения потребляющего сервис
    QTP_ACCESS_TOKEN: "${creds.link('QTP_TOKEN', remoteRefKey: {{ current_env.additionalTemplateVariables.qtp.cluster }}/{{ current_env.additionalTemplateVariables.qtp.env }}/{{ current_env.additionalTemplateVariables.qtp.env }}-qtp/QTP).password}" # ocp-10/qtp-env/qtp-ns/QTP
    ```

4. При использование макроса указателя (например, `${STORAGE_PASSWORD}`) на параметр, заданный через Cred snippet при вычисление `<remoteRefKey>` EnvGene учитывает объект на котором определен параметр на который указывается.

#### [Option 1] Parameter in Effective Set

1. Значение параметра это Cred snippet в котором:
   1. Отрендерилась Jinja
   2. Заданы дефолтные значения
2. Достаточен для генерации ExternalSecret CR
3. Используется:
   1. The Some Script для создания Cred
   2. Argo Vault Plugin для резолва Cred

```yaml

# AS IS
<parameter-key>: <value>

# TO BE
<parameter-key>: "${creds.link('<cred-id>').<json-path>}"

# Example
QIP_BILL_CREDIT_PASSWORD: "${creds.create('ID_QIP_BILL_CREDIT_CREDS', secretStore: default-store, remoteRefKey: ocp-05/env-1/env-1-bss).password}"
QIP_BILL_CREDIT_USERNAME: "${creds.create('ID_QIP_BILL_CREDIT_CREDS', secretStore: default-store, remoteRefKey: ocp-05/env-1/env-1-bss).username}"
PIM_TOKEN: "${creds.create('PIM_TOKEN', secretStore: default-store, remoteRefKey: ocp-05/design-time/design-time/CloudBSS-PIM, argoResolve: true).password}"
```

### Option 2. With Credential in EnvGene

#### [Option 2] Cred Snippet

В дополнение к уже существующему snippet `creds.get()` для локальных Cred, для интеграции с External Cred Store вводятся два новых snippet:

- `creds.create()`: Для идемпотентного создания Cred в Ext Cred Store и связывания его с параметром
- `creds.link()`: Для связывания параметра с созданным ранее (существующим) Cred в Ext Cred Store

`creds.get()` по-прежнему полностью поддерживается для работы с локальными Cred.

```yaml
# AS IS Cred snippet
<parameter-key>: "${creds.get('<cred-id>').secret|username|password}"

# TO BE Cred snippet
<parameter-key>: "${creds.get|link|create('<cred-id>', argoResolve: false).<json-path>}"

# Example
global.secrets.streamingPlatform.password: "${creds.create('cdc-streaming-cred').password}"
global.secrets.streamingPlatform.username: "${creds.create('cdc-streaming-cred').username}"
TOKEN: "${creds.link('app-cred', argoResolve: false)}"
```

1. Cred snippet задается в значение параметра в:
   1. EnvGene template
   2. Environment specific parameter set
2. Cred snippet содержит:
   1. Обязательный аттрибут `<cred-id>`, который указывает на Credential Template
   2. Опциональный аттрибут `<json-path>`, который определяет JSON path в значение Cred
   3. Опциональный аттрибут `argoResolve: true|false`, который определяет, кто будет обрабатывать данный snippet в деплоймент контексте

#### [Option 2] Credential Template

1. Credential Template это отдельный Jinja шаблон, использующий EnvGene macros
2. Содержит описание только экстернал Creds
3. Создается вручную
4. Должен содержать все Cred используемые в энве

```yaml
dbaas-creds:
  type: external
  secretStore: non-default
  remoteRefKey: {{ current_env.cloud }}

ID_AUTH_CLIENT_CREDS:
  type: external
  secretStore: non-default
  remoteRefKey: {{ current_env.additionalTemplateVariables.qms-cred-ref }}

ID_AUTH_CREDS:
  type: external
  secretStore: envgeneNullValue
  remoteRefKey: envgeneNullValue

ID_QIP_BILL_CREDIT_CREDS:
  type: external
  secretStore: default-store
  remoteRefKey: {{ current_env.cloud }}/{{ current_env.name }}/{{ current_env.name }}-bss

PIM_TOKEN:
  type: external
  secretStore: default-store
  remoteRefKey: {{ current_env.cloud }}/design-time

QTP_TOKEN:
  type: external
  secretStore: default-store
  remoteRefKey: {{ current_env.additionalTemplateVariables.qtp.cluster }}/{{ current_env.additionalTemplateVariables.qtp.env }}/{{ current_env.additionalTemplateVariables.qtp.env }}-qtp/QTP
```

#### [Option 2] Credential

В дополнение к существующим Credential которые генерятся для каждого уникального `creds.get(<cred-id>)` в тот же самый Credential файл энва дополнителльно генерируются Credential из темплейта

1. Генерируется EnvGene процессе генерации энв инстанса на основе Cred Template (просто рендерится Jinja) и сохраняются в инстансном репозитории
2. Префикс уникальности Cred не используется при `creds`

```yaml

# AS IS Cred
<cred-id>:
  type: usernamePassword|secret
  data:
    username: string
    password: string
    secret: string

# TO BE Cred
<cred-id>:
  type: usernamePassword|secret|external
  secretStore: string
  remoteRefKey: string
  argoResolve: boolean
  data:
    username: string
    password: string
    secret: string

# Example

<cred-id>:
  type: external
  secretStore: string
  remoteRefKey: string
  argoResolve: boolean

dbaas-creds:
  type: external
  secretStore: default-store
  remoteRefKey: ocp-05/platform-01/platform-01-dbaas/dbaas
  argoResolve: false

cdc-streaming-cred:
  type: external
  secretStore: default-store
  remoteRefKey: ocp-05/env-1/env-1-data-management/cdc
  argoResolve: true

app-cred:
  type: external
  secretStore: custom-store
  remoteRefKey: very/special/path
  argoResolve: true
```

#### [Option 2] Parameter in Effective Set

1. Значение параметра это Cred snippet, который сенеририрован на основе:
   1. Credential
   2. Cred Snippet
2. Достаточен для генерации ExternalSecret CR
3. Используется:
   1. The Some Script для создания Cred
   2. Argo Vault Plugin для резолва Cred
4. Cred snippet содержит:
   1. Обязательный аттрибут `<cred-id>`
   2. Обязательный аттрибут `secretStore`
   3. Обязательный аттрибут `remoteRefKey`
      1. В качестве сепаратора уровней иерархической структуры хранения используется `/`
      2. Лидирующий `/` не задается
   4. Обязательный аттрибут `<json-path>`, который определяет JSON path в значение Cred
   5. Опциональный аттрибут `argoResolve: true|false`, который определяет, кто будет обрабатывать данный snippet в деплоймент контекст. Обрабатывается Argo компонентами.

```yaml
# AS IS
<parameter-key>: <value>

# TO BE
<parameter-key>: "${creds.link('<cred-id>').<json-path>}"

# Example
QIP_BILL_CREDIT_PASSWORD: "${creds.create('ID_QIP_BILL_CREDIT_CREDS', secretStore: default-store, remoteRefKey: ocp-05/env-1/env-1-bss).password}"
QIP_BILL_CREDIT_USERNAME: "${creds.create('ID_QIP_BILL_CREDIT_CREDS', secretStore: default-store, remoteRefKey: ocp-05/env-1/env-1-bss).username}"
PIM_TOKEN: "${creds.create('PIM_TOKEN', secretStore: default-store, remoteRefKey: ocp-05/design-time/design-time/CloudBSS-PIM).password}"
```

### Option 1 vs Option 2

| Критерий                       | Option 1. Without Credential in EnvGene       | Option 2. With Credential in EnvGene              |
|--------------------------------|-----------------------------------------------|---------------------------------------------------|
| **Простота конфигурации**      | Низкая (много параметров в snippet)           | Высокая (параметры в template)                    |
| **Траблшут**                   | Сложнее (нужно искать по всем параметрам)     | Проще (все в Credential файле)                    |
| **Централизация конфигурации** | Низкая (разбросана по параметрам)             | Высокая (в Credential Template)                   |
| **Гибкость**                   | Одинаковая                                    | Одинаковая                                        |
| **Валидация**                  | Сложная (нужно собирать из разных мест)       | Простая (все в одном месте)                       |
| **Миграция**                   | ???                                           | ???                                               |
| **Сложность реализации**       | Средняя                                       | Высокая (нужна поддержка Credential Template)     |

### `ExternalSecret` CR

1.Генерируется by The Some Script на основе Credentials

```yaml
---
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: <cred-id>
spec:
  secretStoreRef:
    name: <secret-store>
    kind: SecretStore
  target:
    ...
  data:
    - # When <json-path> is not present - secretKey: <cred-id>
      secretKey: <cred-id>.<json-path>
      remoteRef:
        key: <<remote-ref-key>>
        # Optional
        # Used only if <json-path> is specified
        property: <json-path>

# Example. Username + Password
---
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: dbaas-creds
spec:
  secretStoreRef:
    name: default-store
    kind: SecretStore
  target:
    ...
  data:
    - secretKey: dbaas-creds.username
      remoteRef:
        key: ocp-05/platform-01/platform-01-dbaas/dbaas
        property: username
    - secretKey: dbaas-creds.password  
      remoteRef:
        key: ocp-05/platform-01/platform-01-dbaas/dbaas
        property: password

---
# Example. No <json-path>
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: consul-cred
spec:
  secretStoreRef:
    name: default-store
    kind: SecretStore
  target:
    ...
  data:
    - secretKey: consul-cred
      remoteRef:
        key: ocp-05

```

### KV Store Structure

Расположение Cred в структуре KV Store определяется на этапе создания Cred, т.е при деплое системы/приложения которую этот Cred описывает.

```text
├── <non-cloud-system> # рефы на эти Cred не генерируются EnvGene
└── <cloud-name>
    └── <environment-name>
          └── <namespace>
              └── <application>
```

Example:

```text
├── ???
└── ocp-05
    └── platform-01
          └── platform-01-dbaas
              └── dbaas
```

> [!NOTE] Инстансный репозиторий одного из проектов:
> Средняя длинна - 73 chars
> Максимальная - 92 chars

### Secret Store

1. Отдельный объект в EnvGene не моделируется
2. Secret Store CR Создается через деплой специального приложения
3. Деплоймент параметры этого приложения управляются в EnvGene

### EnvGene System Creds

EnvGene System Creds — это Creds, необходимые для работы самого EnvGene, например, Creds для доступа к registry или токен GitLab для выполнения коммитов.

Short term - значение храниться в CI/CD переменных EnvGene репозитория

Long term - использование общей библиотеки для интеграции

### Transformer

TBD

### Migration

TBD

### Use Cases

1. Adding a sensitive parameter
2. Deleting a sensitive parameter
3. Modifying the value of a sensitive parameter (out of scope for EnvGene)
4. Migration from local to external Cred storage
