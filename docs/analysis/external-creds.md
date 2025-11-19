# External Creds

- [External Creds](#external-creds)
  - [Problem Statement](#problem-statement)
  - [Open Question](#open-question)
  - [Limitation](#limitation)
  - [Assumption](#assumption)
  - [Proposed Approach](#proposed-approach)
    - [Option 1. Without Credential in EnvGene. String notated Cred snippet](#option-1-without-credential-in-envgene-string-notated-cred-snippet)
      - [\[Option 1\] Cred Snippet](#option-1-cred-snippet)
      - [\[Option 1\] Parameter in Effective Set](#option-1-parameter-in-effective-set)
    - [Option 2. With Credential in EnvGene. String notated Cred snippet](#option-2-with-credential-in-envgene-string-notated-cred-snippet)
      - [\[Option 2\] Cred Snippet](#option-2-cred-snippet)
      - [\[Option 2\] Credential Template](#option-2-credential-template)
      - [\[Option 2\] Credential](#option-2-credential)
      - [\[Option 2\] Parameter in Effective Set](#option-2-parameter-in-effective-set)
    - [Option 3. With Credential in EnvGene. Object notated Cred snippet](#option-3-with-credential-in-envgene-object-notated-cred-snippet)
      - [\[Option 3\] Cred Snippet](#option-3-cred-snippet)
      - [\[Option 3\] Credential Template](#option-3-credential-template)
      - [\[Option 3\] Credential](#option-3-credential)
      - [\[Option 3\] Parameter in Effective Set](#option-3-parameter-in-effective-set)
    - [Option 1 vs Option 2](#option-1-vs-option-2)
    - [`ExternalSecret` CR](#externalsecret-cr)
    - [KV Store Structure](#kv-store-structure)
    - [Secret Store](#secret-store)
    - [EnvGene System Creds](#envgene-system-creds)
    - [Transformer](#transformer)
    - [Migration](#migration)
    - [Use Cases](#use-cases)

## Problem Statement

На данный момент EnvGene управляет только Credentials, которые размещаются в файлах EnvGene репозитория. Интеграция с внешними Secret Store (например, Vault, AWS Secrets Manager, Azure Key Vault, GCP Secret Manager) отсутствует. В результате:

1. EnvGene не подходит для проектов, где запрещено хранить секретные параметры в GIT, даже в зашифрованном виде.
2. Нет инструментов для централизованной ротации Credentials.

Требуется доработать EnvGene, чтобы он мог описывать, валидировать и использовать Credentials, которые физически хранятся во внешних Secret Store, при этом сохраняя обратную совместимость с локальными Credential.

## Open Question

- [ ] Что делать с аттрибутами `defaultCredentialsId`, `maasConfig.credentialsId` Cloud и Namespace? Оставить как есть или задавать через Cred snippet
- [ ] Допустим ли тот факт, что переход на Ext Store потребует изменений в темплейтах?
- [+] Должен быть отдельно `creds.link` и `creds.create`
  - Да
- [+] Нужно ли копировать Credentials в Effective Set директорию? Следует ли указывать ссылку на файл с Credentials окружения в каком-либо параметре (например, ввести metadata-файл с указанием версии)?
  - Credentials не копируются и ссылка не указывается. EnvGene генерирует Cred snippet, достаточный для формирования ExternalSecret CR.
- [ ] Одинаковый ли Cred Snippet используется в шаблоне и Effective Set?
- [ ] Какие нужны валидации?
- [+] `remoteRef.key` это про изоляцию?
   1. Да. Это иерархический способ хранения, на основе которого можно построить политики доступа
- [ ] Подерживает ли Azure `<json-path>`
- [ ] Какие ограничения на имя креда? Такие же как и для `remoteRef.key`?
- [ ] Какая структура хранения Creds для non-cloud систем?
- [ ] Должен ли secret store моделироваться в EnvGene?
- [ ] Как реализовать автоматизированное создание Cred Store на основе Creds, в которых он упоминается
- [ ] Валидация части параметров EnvGene на основании расширяемых схем (например, проверять параметры dbaas по специализированной схеме dbaas)
  - Стоит ли?
  - Как?
- [ ] Должны ли быть ссылки между параметрами разных приложений
- [ ] Стоит ли заменить ${creds} -> $type
- [+] Опция 1 или Опция 2
  - 2
- [+] Должен ли быть аттрибут `create` свойством Cred
  - Да
- [+] Должен ли быть аттрибут `secret-store` свойством Cred
  - Да
- [ ] Имплементация Transformer
  - Какой алгоритм нормализации?
  - Должен ли `remoteRef.key` быть в модели EnvGene строкой и/или объектом
- [ ] Должна ли нормализация `remoteRef.key` происходить в EnvGene

## Limitation

1. Один секрет на путь KV store

## Assumption

1. Трансформаторы нормализуют `remoteRef`, т.е.:
   1. Приводит к виду `0-9`, `a-z`, `A-Z`, `-`
   2. Обеспечивает 127 Char Limit
2. Имя кластера и Cloud совпадают
3. Cred должен создаваться `creds.create()` до его использования `creds.link()`
4. При переходе на External Cred Store необходимо изменение EnvGene template
5. Уникальность Cred в `<secret-store>` определяется через `<remote-ref-key>`

## Proposed Approach

![external-cred](/docs/images/external-cred.png)
![external-cred-transformation](/docs/images/external-cred-transformation.png)

### Option 1. Without Credential in EnvGene. String notated Cred snippet

#### [Option 1] Cred Snippet

В дополнение к уже существующему snippet `creds.get()` для локальных Cred, для интеграции с External Cred Store вводятся два новых snippet:

- `creds.create()`: Для идемпотентного создания Cred в Ext Cred Store и связывания его с параметром
- `creds.link()`: Для связывания параметра с созданным ранее (существующим) Cred в Ext Cred Store

`creds.get()` по-прежнему полностью поддерживается для работы с локальными Cred.

```yaml
# AS IS Cred snippet
<parameter-key>: "${creds.get('<cred-id>').secret|username|password}"

# TO BE Cred snippet
<parameter-key>: "${creds.get|link|create('<cred-id>', secretStore: '<secret-store>', remoteRefKey: '<remote-ref-key>', credHandler: argo|eso).<json-path>}"

# Example
global.secrets.streamingPlatform.password: "${creds.create('cdc-streaming-cred', remoteRefKey: {{ current_env.cloud }}/{{ current_env.name }}/{{ current_env.name }}-bss ).password}"
global.secrets.streamingPlatform.username: "${creds.create('cdc-streaming-cred', remoteRefKey: {{ current_env.cloud }}/{{ current_env.name }}/{{ current_env.name }}-bss ).username}"
TOKEN: "${creds.link('app-cred', secretStore: custom-store, remoteRefKey: very/special/path, credHandler: eso)}"
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
   5. Опциональный аттрибут `credHandler: argo|eso`, который определяет, кто будет обрабатывать данный snippet в effective set (создавать ExternalSecret CR): `argo` - Argo Vault Plugin, `eso` - External Secret Operator.
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
PIM_TOKEN: "${creds.create('PIM_TOKEN', secretStore: default-store, remoteRefKey: ocp-05/design-time/design-time/CloudBSS-PIM, credHandler: argo).password}"
```

### Option 2. With Credential in EnvGene. String notated Cred snippet

#### [Option 2] Cred Snippet

В дополнение к уже существующему snippet `creds.get()` для локальных Cred, для интеграции с External Cred Store вводятся два новых snippet:

- `creds.create()`: Для идемпотентного создания Cred в Ext Cred Store и связывания его с параметром
- `creds.link()`: Для связывания параметра с созданным ранее (существующим) Cred в Ext Cred Store

`creds.get()` по-прежнему полностью поддерживается для работы с локальными Cred.

```yaml
# AS IS Cred snippet
<parameter-key>: "${creds.get('<cred-id>').secret|username|password}"
```

```yaml
# TO BE Cred snippet. 
<parameter-key>: "${creds.get|link|create('<cred-id>', credHandler: argo|eso).<json-path>}"

# Example
global.secrets.streamingPlatform.username: "${creds.create('cdc-streaming-cred').username}"
global.secrets.streamingPlatform.password: "${creds.create('cdc-streaming-cred').password}"

TOKEN: "${creds.link('app-cred', credHandler: eso)}"

DBAAS_CLUSTER_DBA_CREDENTIALS_USERNAME: ${creds.create('dbaas-creds', remoteRefKey: {{ current_env.cloud }}).username}
DBAAS_CLUSTER_DBA_CREDENTIALS_PASSWORD: ${creds.create('dbaas-creds', remoteRefKey: {{ current_env.cloud }}).password}
```

1. Cred snippet задается в значение параметра в:
   1. EnvGene template
   2. Environment specific parameter set
2. Cred snippet содержит:
   1. Обязательный аттрибут `<cred-id>`, который указывает на Credential Template
   2. Опциональный аттрибут `<json-path>`, который определяет JSON path в значение Cred
   3. Опциональный аттрибут `credHandler: argo|eso`, который определяет, кто будет обрабатывать данный snippet в effective set (создавать ExternalSecret CR): `argo` - Argo Vault Plugin, `eso` - External Secret Operator.

#### [Option 2] Credential Template

1. Credential Template это отдельный Jinja шаблон, использующий EnvGene macros
2. Содержит описание только экстернал Creds
3. Создается вручную
4. Должен содержать все Cred используемые в энве

```yaml
# Example
cdc-streaming-cred:
  type: external
  create: true
  secretStore: default-store
  remoteRefKey: {{ current_env.cloud }}/{{ current_env.name }}/{{ current_env.name }}-data-management/cdc

app-cred:
  type: external
  secretStore: custom-store
  remoteRefKey: very/special/path
  credHandler: argo

dbaas-creds:
  type: external
  create: true
  secretStore: default-store
  remoteRefKey: {{ current_env.cloud }}
```

#### [Option 2] Credential

В дополнение к существующим Credential которые генерируются для каждого уникального `creds.get(<cred-id>)` в тот же самый Credential файл энва дополнительно генерируются Credential из темплейта

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
```

```yaml
# TO BE Cred
<cred-id>:
  # Mandatory
  type: usernamePassword|secret|external
  # Mandatory for external
  secretStore: string
  # Mandatory for external
  remoteRefKey: string
  # Optional for external
  create: boolean
  # Not used for external
  data:
    username: string
    password: string
    secret: string

# Example
dbaas-creds:
  type: external
  create: true
  secretStore: default-store
  remoteRefKey: ocp-05

cdc-streaming-cred:
  type: external
  create: true
  secretStore: default-store
  remoteRefKey: ocp-05/env-1/env-1-data-management/cdc

app-cred:
  type: external
  secretStore: custom-store
  remoteRefKey: very/special/path
  credHandler: argo
```

#### [Option 2] Parameter in Effective Set

1. Значение параметра это Cred snippet, который сгенерирован на основе:
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
   4. Опциональный аттрибут `<json-path>`, который определяет JSON path в значение Cred
   5. Опциональный аттрибут `credHandler: argo|eso`, который определяет, кто будет обрабатывать данный snippet в effective set (создавать ExternalSecret CR): `argo` - Argo Vault Plugin, `eso` - External Secret Operator.

```yaml
# TO BE Cred snippet. 
<parameter-key>: "${creds.get|link|create('<cred-id>', secretStore: '<secret-store>', remoteRefKey: '<remote-ref-key>', credHandler: argo|eso).<json-path>}"

# Example
global.secrets.streamingPlatform.username: "${creds.create('cdc-streaming-cred', secretStore: default-store, remoteRefKey: ocp-05/env-1/env-1-data-management/cdc).username}"
global.secrets.streamingPlatform.password: "${creds.create('cdc-streaming-cred', secretStore: default-store, remoteRefKey: ocp-05/env-1/env-1-data-management/cdc).password}"

TOKEN: "${creds.link('app-cred', secretStore: custom-store, remoteRefKey: very/special/path, credHandler: eso).password}"

DBAAS_CLUSTER_DBA_CREDENTIALS_USERNAME: "${creds.create('dbaas-creds', secretStore: default-store, remoteRefKey: ocp-05).username}"
DBAAS_CLUSTER_DBA_CREDENTIALS_PASSWORD: "${creds.create('dbaas-creds', secretStore: default-store, remoteRefKey: ocp-05).password}"
```

### Option 3. With Credential in EnvGene. Object notated Cred snippet

#### [Option 3] Cred Snippet

Object notated Cred snippet используется для декларативного задания параметров, получаемых из External Cred Store, в виде YAML-объекта.

Object Cred snippet задается в значение параметра в:

1. EnvGene template
2. Environment specific parameter set

`creds.get()` по-прежнему полностью поддерживается для работы с локальными Cred.

```yaml
# AS IS Cred snippet
<parameter-key>: "${creds.get('<cred-id>').secret|username|password}"
```

```yaml
# TO BE Cred snippet.
<parameter-key>:
  $type: enum[credential]
  # Mandatory
  # Pointer to EnvGene Credential
  credId: string
  # Optional
  # Path to the specific value inside the secret
  jsonPath: string
  # Optional
  # Cred snippet handler - Argo Vault Plugin or External Secrets Operator
  credHandler: enum[argo, eso]

# Example
global.secrets.streamingPlatform.username:
  $type: credential
  credId: cdc-streaming-cred
  jsonPath: username

global.secrets.streamingPlatform.password:
  $type: credential
  credId: cdc-streaming-cred
  jsonPath: password

TOKEN:
  $type: credential
  credId: app-cred
  credHandler: eso
  jsonPath: password

DBAAS_CLUSTER_DBA_CREDENTIALS_USERNAME:
  $type: credential
  credId: dbaas-creds
  jsonPath: username

DBAAS_CLUSTER_DBA_CREDENTIALS_PASSWORD:
  $type: credential
  credId: dbaas-creds
  jsonPath: password
```

#### [Option 3] Credential Template

1. Credential Template это отдельный Jinja шаблон, использующий EnvGene macros
2. Содержит описание только экстернал Creds
3. Создается вручную
4. Должен содержать все Cred используемые в энве

```yaml
# Example
cdc-streaming-cred:
  type: external
  create: true
  secretStore: default-store
  remoteRefKey: {{ current_env.cloud }}/{{ current_env.name }}/{{ current_env.name }}-data-management/cdc

app-cred:
  type: external
  secretStore: custom-store
  remoteRefKey: very/special/path
  credHandler: argo

dbaas-creds:
  type: external
  create: true
  secretStore: default-store
  remoteRefKey: {{ current_env.cloud }}
```

#### [Option 3] Credential

В дополнение к существующим Credential которые генерируются для каждого уникального `creds.get(<cred-id>)` в тот же самый Credential файл энва дополнительно генерируются Credential из темплейта

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
```

```yaml
# TO BE Cred
<cred-id>:
  # Mandatory
  type: usernamePassword|secret|external
  # Mandatory for external
  secretStore: string
  # Mandatory for external
  remoteRefKey: string
  # Optional for external
  create: boolean
  # Not used for external
  data:
    username: string
    password: string
    secret: string

# Example
dbaas-creds:
  type: external
  create: true
  secretStore: default-store
  remoteRefKey: ocp-05/platform-01/platform-01-dbaas/dbaas

cdc-streaming-cred:
  type: external
  create: true
  secretStore: default-store
  remoteRefKey: ocp-05/env-1/env-1-data-management/cdc

app-cred:
  type: external
  secretStore: custom-store
  remoteRefKey: very/special/path
  credHandler: argo
```

#### [Option 3] Parameter in Effective Set

1. Значение параметра это Cred snippet, который сенеририрован на основе:
   1. Credential
   2. Cred Snippet
2. Достаточен для генерации ExternalSecret CR
3. Используется:
   1. The Some Script для создания Cred
   2. Argo Vault Plugin для резолва Cred

```yaml
# TO BE Cred snippet.
<parameter-key>:
  # Mandatory
  # Pointer to EnvGene Credential
  $type: enum[credential]
  # Mandatory
  secretStore: string
  # Mandatory
  remoteRefKey: string
  # Optional
  # Path to the specific value inside the secret
  jsonPath: string
  # Optional
  # Cred snippet handler - Argo Vault Plugin or External Secrets Operator
  credHandler: enum[argo, eso]

# Example
global.secrets.streamingPlatform.username:
  $type: credential
  credId: cdc-streaming-cred
  jsonPath: username

global.secrets.streamingPlatform.password:
  $type: credential
  credId: cdc-streaming-cred
  jsonPath: password

TOKEN:
  $type: credential
  credId: app-cred
  credHandler: eso
  jsonPath: password

DBAAS_CLUSTER_DBA_CREDENTIALS_USERNAME:
  $type: credential
  credId: dbaas-creds
  jsonPath: username

DBAAS_CLUSTER_DBA_CREDENTIALS_PASSWORD:
  $type: credential
  credId: dbaas-creds
  jsonPath: password
```

### Option 1 vs Option 2

| Критерий                       | Option 1. Without Credential in EnvGene       | Option 2. With Credential in EnvGene              |
|--------------------------------|-----------------------------------------------|---------------------------------------------------|
| **Централизация конфигурации** | Низкая (разбросана по параметрам)             | Высокая (в Credential Template)                   |
| **Простота конфигурации**      | Низкая (много параметров в snippet)           | Высокая (параметры в template)                    |
| **Траблшут**                   | Сложнее (нужно искать по всем параметрам)     | Проще (все в Credential файле)                    |
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
        key: <remote-ref-key>
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
2. Secret Store CR создается через деплой специального приложения
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
