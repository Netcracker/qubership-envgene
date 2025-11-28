# External Credentials

- [External Credentials](#external-credentials)
  - [Problem Statement](#problem-statement)
  - [Open Question](#open-question)
  - [Limitation](#limitation)
  - [Assumption](#assumption)
  - [Proposed Approach](#proposed-approach)
    - [Option 1. String macro, no Credential Template](#option-1-string-macro-no-credential-template)
      - [\[Option 1\] Credential macro](#option-1-credential-macro)
      - [\[Option 1\] Parameter in Effective Set](#option-1-parameter-in-effective-set)
    - [Option 2. String macro + Credential Template](#option-2-string-macro--credential-template)
      - [\[Option 2\] Credential macro](#option-2-credential-macro)
      - [\[Option 2\] Credential Template](#option-2-credential-template)
      - [\[Option 2\] Credential](#option-2-credential)
      - [\[Option 2\] Parameter in Effective Set](#option-2-parameter-in-effective-set)
    - [Option 3. Object macro + Credential Template](#option-3-object-macro--credential-template)
      - [\[Option 3\] Credential macro](#option-3-credential-macro)
      - [\[Option 3\] Credential Template](#option-3-credential-template)
      - [\[Option 3\] Credential](#option-3-credential)
      - [\[Option 3\] Parameter in Effective Set](#option-3-parameter-in-effective-set)
    - [`ExternalSecret` CR](#externalsecret-cr)
    - [KV Store Structure](#kv-store-structure)
    - [Secret Store](#secret-store)
    - [EnvGene System Credentials](#envgene-system-credentials)
    - [Validation](#validation)
    - [Transformer](#transformer)
    - [Migration](#migration)
    - [Use Cases](#use-cases)

## Problem Statement

На данный момент EnvGene управляет только Credentials, которые размещаются в файлах EnvGene репозитория. Интеграция с внешними Secret Store (например, Vault, AWS Secrets Manager, Azure Key Vault, GCP Secret Manager) отсутствует. В результате:

1. EnvGene не подходит для проектов, где запрещено хранить секретные параметры в GIT, даже в зашифрованном виде.
2. Нет инструментов для централизованной ротации Credentials.

Требуется доработать EnvGene, чтобы он мог описывать, валидировать и использовать Credentials, которые физически хранятся во внешних Secret Store, при этом сохраняя обратную совместимость с локальными Credential.

## Open Question

- [x] Что делать с аттрибутами `defaultCredsId`, `maasConfig.credentialsId` Cloud и Namespace? Оставить как есть или задавать через Credential macro
  - В рамках эпика мы должны иметь возможность описать такие параметры через credRef (сохранив обратную совместимость с текущим подходом)
- [x] Допустим ли тот факт, что переход на Ext Store потребует изменений в темплейтах?
  - Вариант без изменения темплейта не известен
- [x] Должен быть отдельно `creds.link` и `creds.create`
  - Нет
- [x] Нужно ли копировать Credentials в Effective Set директорию? Следует ли указывать ссылку на файл с Credentials окружения в каком-либо параметре (например, ввести metadata-файл с указанием версии)?
  - Credentials не копируются и ссылка не указывается. EnvGene генерирует Credential macro, достаточный для формирования ExternalSecret CR.
- [x] Одинаковый ли Credential macro используется в шаблоне и Effective Set?
  - используются макросы разных типов `extCredRef`, `credRef`
- [x] Опция 1 или Опция 2 или Опция 3
  - 3
- [x] Должен ли быть аттрибут `create` свойством Credential
  - Да
- [x] Должен ли быть аттрибут `secret-store` свойством Credential
  - Да
- [x] `remoteRef.key` это про изоляцию?
   1. Да. Это иерархический способ хранения, на основе которого можно построить политики доступа
- [x] Какие ограничения на имя Credential? Такие же как и для `remoteRef.key`?
  - Да
- [x] Поддерживает ли Azure `jsonPath`
  - Нет, только Vault
- [x] Можем ли мы использовать [JSON path](https://support.smartbear.com/alertsite/docs/monitors/api/endpoint/jsonpath.html)
  - не можем
- [ ] Как реализовать автоматизированное создание Credential Store на основе Credentials, в которых он упоминается
- [ ] Валидация части параметров EnvGene на основании расширяемых схем (например, проверять параметры dbaas по специализированной схеме dbaas)
  - Стоит ли?
  - Как?
- [ ] Должны ли быть ссылки между параметрами разных приложений
- [ ] Какие нужны валидации?

---

- [ ] Должен ли Secret Store моделироваться в EnvGene?
- [ ] Куда в Effective Set сохранять параметры описанные через Credential macro?
  - отдельные файлы, как сейчас
  - вместе с остальными
- [ ] Какая структура хранения Credentials в Secret Store для non-cloud систем?
- [ ] Имплементация Transformer
  - Какой алгоритм нормализации?
  - Должна ли нормализация `remoteRef.key` происходить в EnvGene?

## Limitation

1. Один секрет на путь KV store

## Assumption

1. Трансформаторы нормализуют `remoteRef`, т.е.:
   1. Приводит к виду `0-9`, `a-z`, `A-Z`, `-`
   2. Обеспечивает 127 Char Limit
2. Имя кластера и Cloud совпадают
3. При переходе на External Credential Store необходимо изменение EnvGene template
4. Уникальность Credential в `secretStore` определяется через `remoteRefKey`
5. Уникальность Credential в EnvGene в пределах EnvGene репозитория определяется через `credId`
6. Уникальность имени ExternalSecret в пределах k8s namespace определяется через нормализованный `credId` + hash от (`secretStore` + `remoteRefKey`)

## Proposed Approach

![external-cred-transformation](/docs/images/external-cred-transformation.png)

---
![external-cred](/docs/images/external-cred.png)

### Option 1. String macro, no Credential Template

#### [Option 1] Credential macro

В дополнение к уже существующему macro `creds.get()` для локальных Credential, для интеграции с External Credential Store вводятся два новых macro:

- `creds.create()`: Для идемпотентного создания Credential в Ext Credential Store и связывания его с параметром
- `creds.link()`: Для связывания параметра с созданным ранее (существующим) Credential в Ext Credential Store

`creds.get()` по-прежнему полностью поддерживается для работы с локальными Credential.

```yaml
# AS IS Credential macro
<parameter-key>: "${creds.get('<cred-id>').secret|username|password}"

# TO BE Credential macro
<parameter-key>: "${creds.get|link|create('<cred-id>', secretStore: '<secret-store>', remoteRefKey: '<remote-ref-key>', credHandler: argo|eso).<json-path>}"

# Example
global.secrets.streamingPlatform.password: "${creds.create('cdc-streaming-cred', remoteRefKey: {{ current_env.cloud }}/{{ current_env.name }}/{{ current_env.name }}-bss ).password}"
global.secrets.streamingPlatform.username: "${creds.create('cdc-streaming-cred', remoteRefKey: {{ current_env.cloud }}/{{ current_env.name }}/{{ current_env.name }}-bss ).username}"
TOKEN: "${creds.link('app-cred', secretStore: custom-store, remoteRefKey: very/special/path, credHandler: eso)}"
```

1. Credential macro задается в значение параметра в:
   1. EnvGene template
   2. Environment specific parameter set
2. Credential macro содержит:
   1. Обязательный аттрибут `<cred-id>`
   2. Опциональный аттрибут `secretStore`
      1. Значение по умолчанию - `default-store`
   3. Опциональный аттрибут `remoteRefKey`
      1. В качестве сепаратора уровней иерархической структуры хранения используется `/`
      2. Лидирующий `/` не задается
      3. Значение по умолчанию, зависит от EnvGene объекта на котором задан Credential через `creds.create()`:
         1. Tenant, Cloud -> `<cloud-name>`
         2. Namespace -> `<cloud-name>/<env-name>/<namespace-name>`
         3. Application -> `<cloud-name>/<env-name>/<namespace-name>/<application-name>`
      4. При использование `creds.link()` значение по умолчанию - `<cloud-name>`
   4. Опциональный аттрибут `<json-path>`, который определяет JSON path в значение Credential
   5. Опциональный аттрибут `credHandler: argo|eso`, который определяет, кто будет обрабатывать данный macro в effective set (создавать ExternalSecret CR): `argo` - Argo Vault Plugin, `eso` - External Secret Operator.
3. Credential macro позволяет использовать EnvGene макросы для параметризации:

    ```yaml
    # Бизнес солюшен -> Платформа
    ## Параметры платформенного солюшена
    DBAAS_CLUSTER_DBA_CREDENTIALS_USERNAME: ${creds.create('dbaas-creds', remoteRefKey: {{ current_env.cloud }}).username} # remoteRefKey: ocp-05
    DBAAS_CLUSTER_DBA_CREDENTIALS_PASSWORD: ${creds.create('dbaas-creds', remoteRefKey: {{ current_env.cloud }}).password} # remoteRefKey: ocp-05
    ## Параметры Cloud Passport для бизнес солюшена
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

4. При использование макроса указателя (например, `${STORAGE_PASSWORD}`) на параметр, заданный через Credential macro при вычисление `<remoteRefKey>` EnvGene учитывает объект на котором определен параметр на который указывается.

#### [Option 1] Parameter in Effective Set

1. Значение параметра это Credential macro в котором:
   1. Отрендерилась Jinja
   2. Заданы дефолтные значения
2. Достаточен для генерации ExternalSecret CR
3. Используется:
   1. The Some Script для создания Credential
   2. Argo Vault Plugin для резолва Credential

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

### Option 2. String macro + Credential Template

#### [Option 2] Credential macro

В дополнение к уже существующему macro `creds.get()` для локальных Credential, для интеграции с External Credential Store вводятся два новых macro:

- `creds.create()`: Для идемпотентного создания Credential в Ext Credential Store и связывания его с параметром
- `creds.link()`: Для связывания параметра с созданным ранее (существующим) Credential в Ext Credential Store

`creds.get()` по-прежнему полностью поддерживается для работы с локальными Credential.

```yaml
# AS IS Credential macro
<parameter-key>: "${creds.get('<cred-id>').secret|username|password}"
```

```yaml
# TO BE Credential macro. 
<parameter-key>: "${creds.get|link|create('<cred-id>', credHandler: argo|eso).<json-path>}"

# Example
global.secrets.streamingPlatform.username: "${creds.create('cdc-streaming-cred').username}"
global.secrets.streamingPlatform.password: "${creds.create('cdc-streaming-cred').password}"

TOKEN: "${creds.link('app-cred', credHandler: eso)}"

DBAAS_CLUSTER_DBA_CREDENTIALS_USERNAME: ${creds.create('dbaas-creds', remoteRefKey: {{ current_env.cloud }}).username}
DBAAS_CLUSTER_DBA_CREDENTIALS_PASSWORD: ${creds.create('dbaas-creds', remoteRefKey: {{ current_env.cloud }}).password}
```

1. Credential macro задается в значение параметра в:
   1. EnvGene template
   2. Environment specific parameter set
2. Credential macro содержит:
   1. Обязательный аттрибут `<cred-id>`, который указывает на Credential Template
   2. Опциональный аттрибут `<json-path>`, который определяет JSON path в значение Credential
   3. Опциональный аттрибут `credHandler: argo|eso`, который определяет, кто будет обрабатывать данный macro в effective set (создавать ExternalSecret CR): `argo` - Argo Vault Plugin, `eso` - External Secret Operator.

#### [Option 2] Credential Template

1. Credential Template это отдельный Jinja шаблон, использующий EnvGene macros
2. Содержит описание только экстернал Credentials
3. Создается вручную
4. Должен содержать все Credential используемые в энве

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

1. Генерируется EnvGene процессе генерации энв инстанса на основе Credential Template (просто рендерится Jinja) и сохраняются в инстансном репозитории
2. Префикс уникальности Credential не используется при `creds`

```yaml
# AS IS Credential
<cred-id>:
  type: usernamePassword|secret
  data:
    username: string
    password: string
    secret: string
```

```yaml
# TO BE Credential
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

1. Значение параметра это Credential macro, который сгенерирован на основе:
   1. Credential
   2. Credential macro
2. Достаточен для генерации ExternalSecret CR
3. Используется:
   1. The Some Script для создания Credential
   2. Argo Vault Plugin для резолва Credential
4. Credential macro содержит:
   1. Обязательный аттрибут `<cred-id>`
   2. Обязательный аттрибут `secretStore`
   3. Обязательный аттрибут `remoteRefKey`
      1. В качестве сепаратора уровней иерархической структуры хранения используется `/`
      2. Лидирующий `/` не задается
   4. Опциональный аттрибут `<json-path>`, который определяет JSON path в значение Credential
   5. Опциональный аттрибут `credHandler: argo|eso`, который определяет, кто будет обрабатывать данный macro в effective set (создавать ExternalSecret CR): `argo` - Argo Vault Plugin, `eso` - External Secret Operator.

```yaml
# TO BE Credential macro. 
<parameter-key>: "${creds.get|link|create('<cred-id>', secretStore: '<secret-store>', remoteRefKey: '<remote-ref-key>', credHandler: argo|eso).<json-path>}"

# Example
global.secrets.streamingPlatform.username: "${creds.create('cdc-streaming-cred', secretStore: default-store, remoteRefKey: ocp-05/env-1/env-1-data-management/cdc).username}"
global.secrets.streamingPlatform.password: "${creds.create('cdc-streaming-cred', secretStore: default-store, remoteRefKey: ocp-05/env-1/env-1-data-management/cdc).password}"

TOKEN: "${creds.link('app-cred', secretStore: custom-store, remoteRefKey: very/special/path, credHandler: eso).password}"

DBAAS_CLUSTER_DBA_CREDENTIALS_USERNAME: "${creds.create('dbaas-creds', secretStore: default-store, remoteRefKey: ocp-05).username}"
DBAAS_CLUSTER_DBA_CREDENTIALS_PASSWORD: "${creds.create('dbaas-creds', secretStore: default-store, remoteRefKey: ocp-05).password}"
```

### Option 3. Object macro + Credential Template

#### [Option 3] Credential macro

`credRef` Credential macro (`$type: credRef`) используется для связи параметра на EnvGene объектах с Credential EnvGene объектом.

Такой macro используется для всех видов Credentials (`usernamePassword`, `secret`, `external`).

Для обратной совместимости `creds.get()` по-прежнему полностью поддерживается для работы с локальными Credential.

```yaml
# AS IS Credential macro
<parameter-key>: "${creds.get('<cred-id>').secret|username|password}"
```

```yaml
# TO BE Credential macro.
<parameter-key>:
  # Mandatory
  # Macro type
  $type: credRef
  # Mandatory
  # Pointer to EnvGene Credential
  credId: string
  # Optional
  # Path to the specific value inside the secret
  # For Vault only
  property: enum [username, password]

# Example
global.secrets.streamingPlatform.username:
  $type: credRef
  credId: cdc-streaming-cred
  property: username

global.secrets.streamingPlatform.password:
  $type: credRef
  credId: cdc-streaming-cred
  property: password

TOKEN:
  $type: credRef
  credId: app-cred

DBAAS_CLUSTER_DBA_CREDENTIALS_USERNAME:
  $type: credRef
  credId: dbaas-creds
  property: username

DBAAS_CLUSTER_DBA_CREDENTIALS_PASSWORD:
  $type: credRef
  credId: dbaas-creds
  property: password

DCL_CONFIG_REGISTRY:
  $type: credRef
  credId: artfactoryqs-admin
```

#### [Option 3] Credential Template

1. Credential Template - Jinja шаблон для рендеринга Credential
2. Содержит описание только экстернал Credentials
3. Создается вручную
4. Должен содержать все Credential используемые в энве

```yaml
# Example
cdc-streaming-cred:
  type: external
  create: true
  secretStore: default-store
  remoteRefKey: {{ current_env.cloud }}/{{ current_env.name }}/{{ current_env.name }}-data-management/cdc/cdc-streaming-cred

app-cred:
  type: external
  secretStore: custom-store
  remoteRefKey: very/special/path

dbaas-creds:
  type: external
  create: true
  secretStore: default-store
  remoteRefKey: {{ current_env.cloud }}

artfactoryqs-admin:
  type: external
  secretStore: default-store
  remoteRefKey: services
```

#### [Option 3] Credential

В дополнение к существующим Credential которые генерируются для каждого уникального `creds.get(<cred-id>)` в тот же самый Credential файл энва дополнительно генерируются Credential из темплейта

1. Генерируется EnvGene процессе генерации энв инстанса на основе Credential Template (просто рендерится Jinja) и сохраняются в инстансном репозитории
2. Префикс уникальности Credential не генерируется для `type: external`
<!-- 4. remoteRefKey опционален, по дефолту все до имени аппа -->
<!-- 5. При рендеринге Credential из темплейта, если `type: external` И `create: true` И `remoteRefKey` не задан; используется дефолтное значение:
    `{{ current_env.cloud }}/{{ current_env.name }}/{{ current_namespace.name }}/{{ current_application.name }}` -->

```yaml
# AS IS Credential
<cred-id>:
  type: usernamePassword|secret
  data:
    username: string
    password: string
    secret: string
```

```yaml
# TO BE Credential
<cred-id>:
  # Mandatory
  type: usernamePassword|secret|external
  # Optional
  # Used only for type: external
  # Mandatory for type: external
  secretStore: string
  # Optional
  # Used only for type: external
  # Mandatory for type: external
  remoteRefKey: string
  # Optional
  # Used only for type: external
  # Optional for type: external
  create: boolean
  # Optional
  # Used only for type: usernamePassword, secret
  # Mandatory for type: usernamePassword, secret
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

artfactoryqs-admin:
  type: external
  secretStore: default-store
  remoteRefKey: services
```

#### [Option 3] Parameter in Effective Set

`extCredRef` Credential macro (`$type: extCredRef`) используется для связи параметра в Effective Set с Credential в внешнем хранилище.

1. `extCredRef` Credential macro генерируется EnvGene на основе:
   1. Credential
   2. `credRef` Credential macro
2. Достаточен для генерации ExternalSecret CR
3. Используется:
   1. Argo Vault Plugin для резолва Credential
   2. Helm chart приложения для создания ExternalSecret CR
4. `remoteRefKey` формируется в в зависимости от типа External Store
   1. Vault: `<remoteRefKey>/<credId>-<property>`
   2. AWS: `<remoteRefKey>/<credId>` +512 char
   3. GCP: `<remoteRefKey>/<credId>` 255 char
   4. Azure: `<remoteRefKey>/<credId>` 127 char
5. В деплоймент контексте в зависимости от значения `SECRET_MACRO_HANDLER: enum [argo, eso]` в DD, параметры описанные через cred macro задаются в:
      1. credentials.yaml (макрос обрабатывается argo) ИЛИ
      2. parameters.yaml (макрос обрабатывается eso)
6. Пайплайн контекст содержит:
   1. EnvGene Credentials with `type: external` and `create: true`

```yaml
# TO BE Credential macro.
<parameter-key>:
  # Mandatory
  $type: extCredRef
  # Mandatory
  secretStore: string
  # Mandatory
  remoteRefKey: string

# Vault example
global.secrets.streamingPlatform.username:
  $type: extCredRef
  secretStore: default-store
  remoteRefKey: ocp-05/env-1/env-1-data-management/cdc/cdc-streaming-cred-username

global.secrets.streamingPlatform.password:
  $type: extCredRef
  secretStore: default-store
  remoteRefKey: ocp-05/env-1/env-1-data-management/cdc/cdc-streaming-cred-password

TOKEN:
  $type: extCredRef
  secretStore: custom-store
  remoteRefKey: very/special/path/app-cred

DBAAS_CLUSTER_DBA_CREDENTIALS_USERNAME:
  $type: extCredRef
  secretStore: default-store
  remoteRefKey: ocp-05/platform-01/platform-01-dbaas/dbaas/dbaas-creds-username

DBAAS_CLUSTER_DBA_CREDENTIALS_PASSWORD:
  $type: extCredRef
  secretStore: default-store # не нужен в деплоймент контексте?
  remoteRefKey: ocp-05/platform-01/platform-01-dbaas/dbaas/dbaas-creds-password

DCL_CONFIG_REGISTRY:
  $type: extCredRef
  secretStore: default-store
  remoteRefKey: services/artfactoryqs-admin
```

### `ExternalSecret` CR

1.Генерируется by The Some Script на основе Credentials

```yaml
---
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: credId
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

Расположение Credential в структуре KV Store определяется на этапе создания Credential, т.е при деплое системы/приложения которую этот Credential описывает.

```text
├── services
└── <cluster-name>
    └── <environment-name>
          └── <namespace>
              └── <application>
```

Example:

```text
├── services
|   └── artfactoryqs-admin
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

### EnvGene System Credentials

EnvGene System Credentials — это Credentials, необходимые для работы самого EnvGene, например, Credentials для доступа к registry или токен GitLab для выполнения коммитов.

Short term - значение храниться в CI/CD переменных EnvGene репозитория

Long term - использование общей библиотеки для интеграции

### Validation

TBD

### Transformer

TBD

### Migration

TBD

### Use Cases

1. Adding a sensitive parameter
2. Deleting a sensitive parameter
3. Modifying the value of a sensitive parameter (out of scope for EnvGene)
4. Migration from local to external Credential storage
