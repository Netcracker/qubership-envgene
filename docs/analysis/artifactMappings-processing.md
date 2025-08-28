# qubership:helm.values.artifactMappings процессинг

```json
{
    "artifactRef": "jaeger:80f031da-024c-4748-a1b9-d548a3dd030f", # Mandatory 
    "helmRef": "qubership-jaeger:7f17a6dc-b973-438f-abb7-e0c57a32afc5", # Mandatory 
    "valuesYamlPath": "jaeger.main" # Mandatory
}
```

- не может быть шаренного между сервисами хелм чарта
- может быть шаренный докер имадж между сервисами
- может быть шаренный докер имадж между хелм чартами
- сервис может быть вязан только с одним чартом
- что такое имя и версия сервиса

1. helmRef должен указывать не хелм чарт без дочерних хелм чартов
2. name в Charts.yaml должен совпадать с name артифакта чарта
3. Каждый докер имадж должен в АМ должен быть связан хотя юы с одним хелм чартом
4. Структура ресурсного профиля должена повторять структуру values yaml чарта 

для каждого компонента АМ из списка [..., ..., ...] в цикле по аттрибуту `qubership:helm.values.artifactMappings` этого компонента:

**если `helmRef`** указывает на чарт у которого ЕСТЬ родитель чарт:

   ```text
   ├── deployment
   |   ├── <deployPostfix-01>
   |   |   ├── <application-name-01>
   |   |   |   └── values
   |   |   |       ├── per-service-parameters
   |   |   |       |   ├── <normalized-chart-name> # нормализированный name РОДИТЕЛЬСКОГО `application/vnd.qubership.helm.chart`
   |   |   |       |   |   └── deployment-parameters.yaml
   |   |   |       ├── deployment-parameters.yaml
   |   |   |       ├── collision-deployment-parameters.yaml
   |   |   |       ├── credentials.yaml
   |   |   |       ├── collision-credentials.yaml
   |   |   |       └── deploy-descriptor.yaml
   ```

   1. Добавить в общий `per-service-parameters/<normalized-chart-name>/deployment-parameters.yaml` параметры

      - с компонента указаного в **artifactRef**
      - располагающиеся под:
         - ключом имени `application/vnd.qubership.helm.chart`
         - ключом из **valuesYamlPath**
      - набор параметров зависит от mime-type компонента из **artifactRef**

   2. Добавить в `deploy-descriptor.yaml` параметры

      - с компонента указаного в **artifactRef**
      - располагающиеся под корневым ключом из **valuesYamlPath**
      - набор параметров зависит от mime-type компонента из **artifactRef**

**если helmRef** указывает на чарт у которого НЕТ родителя чарта:

   ```text
   ├── deployment
   |   ├── mapping.yml
   |   ├── <deployPostfix-01>
   |   |   ├── <application-name-01>
   |   |   |   └── values
   |   |   |       ├── per-service-parameters
   |   |   |       |   ├── <normalized-chart-name> # нормализированный name `application/vnd.qubership.helm.chart`
   |   |   |       |   |   └── deployment-parameters.yaml
   |   |   |       |   └── <normalized-chart-name> # нормализированный name `application/vnd.qubership.helm.chart`
   |   |   |       |       └── deployment-parameters.yaml
   |   |   |       ├── deployment-parameters.yaml
   |   |   |       ├── collision-deployment-parameters.yaml
   |   |   |       ├── credentials.yaml
   |   |   |       ├── collision-credentials.yaml
   |   |   |       └── deploy-descriptor.yaml
   ```

   1. Создать отдельный `per-service-parameters/<normalized-chart-name>/deployment-parameters.yaml` и добавить в него параметры

      - с компонента указаного в **artifactRef**
      - располагающиеся под корневым ключом из **valuesYamlPath**
      - набор параметров зависит от `mime-type` компонента из **artifactRef**

   2. Добавить в deploy-descriptor.yaml параметры

      - с компонента указаного в **artifactRef**
      - располагающиеся под корневым ключом из **valuesYamlPath**
      - набор параметров зависит от `mime-type` компонента из **artifactRef**

**если таких компонентов нет** - не делать ничего, не падать

**если qubership:helm.values.artifactMappings** не задан - не делать ничего, не падать
