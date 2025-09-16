# Service Parameters Processing

## Problem Statement

Для подгоовки деплоймент параметров приложения требуется, чтобы система конфигурационного менеджмента формировала параметры, структура которых полностью соответствует структуре Helm-чарта. К таким параметрам относятся:

1. Динамические параметры, связанные с артефактами:
   - Docker-образы
   - ZIP, JAR (Maven-артефакты)

2. Параметры производительности (например, ресурсные профили)

С учетом следующих сценариев:

- Helm-чарт может являться umbrella-чартом (содержать вложенные чарты)
- Один чарт может быть связан с несколькими артефактами

С выполнением слудующих требований:

- Структура values должна повторять структуру Helm-чарта:
  - Для не-umbrella-чарта параметры передаются под ключом, определённым пользователем
  - Для nested-чартов параметры передаются под ключом, соответствующим имени вложенного чарта
- Набор параметров должен быть стандартизован
- Набор параметров должен соответствовать типу артефакта

<!-- ## Use Cases -->

<!-- 1. `application/vnd.qubership.standalone-runnable` depends on ONE `application/vnd.qubership.helm.chart`
2. `application/vnd.qubership.standalone-runnable` depends on MULTIPLE  `application/vnd.qubership.helm.chart`
3. `application/vnd.qubership.standalone-runnable` depends on ONE `application/vnd.qubership.helm.chart`. `application/vnd.qubership.helm.chart` without `qubership:helm.values.artifactMappings` depends on ONE `application/vnd.docker.image`
4. `application/vnd.qubership.standalone-runnable` depends on ONE `application/vnd.qubership.helm.chart`. `application/vnd.qubership.helm.chart` without `qubership:helm.values.artifactMappings` depends on MULTIPLE `application/vnd.docker.image` (not valid)
5. `application/vnd.qubership.standalone-runnable` depends on ONE `application/vnd.qubership.helm.chart`. `application/vnd.qubership.helm.chart` with `qubership:helm.values.artifactMappings` depends on ONE `application/vnd.docker.image`
6. `application/vnd.qubership.standalone-runnable` depends on ONE `application/vnd.qubership.helm.chart`. `application/vnd.qubership.helm.chart` with `qubership:helm.values.artifactMappings` depends on MULTIPLE `application/vnd.docker.image` -->

## Proposed Approach

Предлагается для формирования таких параметров использовать аппликейшен манифест, который будет содержать:

- описание хелм чарта
- описание артифактов
- описание связей между чартом и артифактами

### Динамические параметры артифактов

Использовать аттрибут `qubership:helm.values.artifactMappings` компонента `application/vnd.qubership.helm.chart` аппликейшен манифеста, который описывает идентификатор артифакта (`artifactRef`) и ключ в структуре helm values (`valuesPathPrefix`) под который будут помещены параметры, описывающие артифакт:

```json
{
   "jaeger:80f031da-024c-4748-a1b9-d548a3dd030f": {
      "valuesPathPrefix": "jaeger.main"
      }
}
```

- Зависимость `application/vnd.qubership.helm.chart` на артифакт заданный в `artifactRef` должна быть описана в секции `dependencies`
- name в Charts.yaml должен совпадать с name артифакта чарта
- Каждый докер имадж должен в АМ должен быть связан хотя бы с одним хелм чартом
- `qubership:helm.values.artifactMappings` обязательный аттрибут для `application/vnd.qubership.helm.chart`
- дефолтное значение `valuesPathPrefix` - `.`

![artifactMappings.drawio.png](/docs/images/artifactMappings.drawio.png)

Конфигурейшен менеджмент при генерации эффектив сета должен обрабатывает такой манифест следующем образом:

1. Для каждого `application/vnd.qubership.standalone-runnable` найти депенд компоненты которые non-child `application/vnd.qubership.helm.chart`
2. Для каждого такого `application/vnd.qubership.helm.chart` найти депенд компоненты, которые [`application/vnd.docker.image`]
3. Для каждого такого [`application/vnd.docker.image`]
   1. Найти значение `valuesPathPrefix` по `artifactRef` в аттрибуте `qubership:helm.values.artifactMappings` компонента `application/vnd.qubership.helm.chart`
   2. Добавить параметры [`application/vnd.docker.image`] (набор параметров зависит от mime-type) **под ключ `valuesPathPrefix`** в
         - `/deployment/<deployPostfix>/<runnable-name>/values/per-service-parameters/<non-child-normalized-chart-name>/deployment-parametrs.yaml`
         - `/deployment/<deployPostfix>/<runnable-name>/values/deploy-descriptor.yaml`
4. Для каждого такого `application/vnd.qubership.helm.chart` найти нестед компоненты, которые `application/vnd.qubership.helm.chart`
5. Для каждого такого нестед `application/vnd.qubership.helm.chart` найти депенд компоненты, которые [`application/vnd.docker.image`]
   1. Найти значение `valuesPathPrefix` по `artifactRef` в аттрибуте `qubership:helm.values.artifactMappings` компонента `application/vnd.qubership.helm.chart`
   2. Добавить параметры [`application/vnd.docker.image`] (набор параметров зависит от mime-type) **под ключ `<child-chart-name>`.`valuesPathPrefix`** в
         - `/deployment/<deployPostfix>/<runnable-name>/values/per-service-parameters/<non-child-normalized-chart-name>/deployment-parametrs.yaml`
         - `/deployment/<deployPostfix>/<runnable-name>/values/deploy-descriptor.yaml`

```text
└── deployment
      └── <deployPostfix-01>
         └── <runnable-name>
            └── values
                  ├── per-service-parameters
                  |   └── <non-child-normalized-chart-name> 
                  |       └── deployment-parameters.yaml
                  └── deploy-descriptor.yaml
```

#### `application/vnd.docker.image`

```yaml
artifacts: []
deploy_param: ''
docker_digest: e305076df2205f1e3968bc566a5ee25f185cbc82ede6d20be8a35a98b8570147
docker_registry: registry.qubership.org:11000
docker_repository_name: docker-image-group
docker_tag: docker-image-version
image_name: docker-image-name
name: docker-image-name
full_image_name: registry.qubership.org:11000/docker-image-group/docker-image-name:docker-image-version
image: registry.qubership.org:11000/docker-image-group/docker-image-name:docker-image-version
git_branch: 
git_revision: 
git_url: 
image_type:
promote_artifacts: 
qualifier: 
version: release-2024.3-5.27.0-20241007.132325-6-RELEASE
```

### Перформансные параметры

Использовать ресурс профайл бейслайн и ресурс профайл оверрайд для управления перформансными параметрами

### Ресурс профайл бейслайн

Набор ямл файлов, содержащих **контрактный по ключам** набор перформансных параметров для:

1. каждого отдельного **non nested** `application/vnd.qubership.helm.chart` (Структура Ресурс профайл бейслайн повторяет структуру хелм чарта(структуру values.yaml) )
   1. в эффектив сете `/deployment/<deployPostfix>/<runnable-name>/values/per-service-parameters/<non-child-normalized-chart-name>/resource-profile-baseline.yaml`

   ИЛИ

2. каждого отдельного `application/vnd.qubership.helm.chart` (Структура Ресурс профайл бейслайн повторяет структуру хелм чарта(структуру values.yaml) )

бейслайн:

- Создается владельцем приложения
- Расположен по контрактному пути в репозитори приложения
- При билде апп манифеста контент помещается в компонент `application/vnd.qubership.resource-profile-baseline`
- попадают в эффектив сет не измененными, как файлик контрактного имени
  - `/deployment/<deployPostfix>/<runnable-name>/values/per-service-parameters/<non-child-normalized-chart-name>/deployment-parametrs.yaml`

### Ресурс профайл оверрайд

Конфигурейшен менеджмент объект:

```yaml
name: "dev_over_envgene"
baseline: "dev" # для валидации при применении
description: ""
applications:
  - name: <application-name> # name of `application/vnd.qubership.standalone-runnable` OR  application (== app manifest) name
    services:
      - name: <chart-name> # name of `application/vnd.qubership.helm.chart` (all or non child ???)
        parameters:
          - name: "MEMORY_LIMIT"
            value: "9000Mi"
          - name: "REPLICAS"
            value: "2"
```

ИЛИ

```yaml
name: "dev_over_envgene"
baseline: "dev" # для валидации при применении
applications:
  <application-name>: # name of `application/vnd.qubership.standalone-runnable` OR  application (== app manifest) name
    parameters:
      <path>: # задаются верно пользователем 
        MEMORY_LIMIT: 9000Mi
        REPLICAS: 2
      <path>: # задаются верно пользователем 
        MEMORY_LIMIT: 9000Mi
        REPLICAS: 2
```

ИЛИ

```yaml
name: "dev_over_envgene"
parameters: {}
applications:
  - name: <application-name> # name of `application/vnd.qubership.standalone-runnable` OR  application (== app manifest) name
    parameters:
      <path>: # задаются верно пользователем 
        MEMORY_LIMIT: 9000Mi
        REPLICAS: 2
      <path>: # задаются верно пользователем 
        MEMORY_LIMIT: 9000Mi
        REPLICAS: 2
```

- Создается конфигуратором инстанса приложения
- Менеджится в конфигурейшен менеджмент системе
- попадают в эффектив сет не измененными, как файлик контрактного имени
- создается для части солюшен (неймспейса) или всего солюшена (клауда)

1. Энвген сохраняет бейслайн как файл в гите, как часть энв инстанса на этапе рендеринга темплейта ?
2. Отдельный тул для конструирования оверрайдов ?
   1. передаешь ему SD (где элементы апп манифесты) генерит:
      1. парамсет с контентом из ресурс профайл бейслайн в верной структуре
      2. парамсет без контента в верной структуре
