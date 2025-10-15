# GString to JinJava Translation library

## Description

This library was created out of the need for a softer migration when moving from GStringTemplateEngine to JinJava template engine in context of CMDB. Therefore, only the GString syntax cases that are in the CMDB were taken into account.
It translates to Jinjava syntax from:

- GString templates
- Jinjava templates
- Simple text

## Usage

Due to the fact that it is impossible to directly translate some elements from GString in Jinjava, custom filters and functions have been created for this purpose. Therefore, for the translation to work correctly, they must be set up except in situations where such syntax is not used.

```java
Jinjava jinjava = new Jinjava();
jinjava.registerFilter(new EnvSuffixFilter());
jinjava.registerFilter(new EnvPrefixFilter());
jinjava.registerFunction(Functions.randomFunction());
```

All JinJava extensions are located in `src/main/java/org/qubership/cloud/devops/gstringtojinjavatranslator/jinjava`.

To translate, use the `translate` method of the `GStringToJinJavaTranslator` class

```java
GStringToJinJavaTranslator translator = new GStringToJinJavaTranslator();
String translated = translator.translate("${BASE_DEPLOYER_TIMEOUT ? BASE_DEPLOYER_TIMEOUT : 1}");
```

If data that cannot be translated is submitted to the input, the library throws an exception `TranslationException`.

## Examples

You can find examples of translation cases in the test class `TranslationTests`

## Library Improvement

If you need to improve the library when there are not enough cases, then first you need to make sure that these cases are covered by the grammar in `src/main/antlr4/org/qubership/cloud/devops/gstringtojinjavatranslator/`.

If this coverage is sufficient, then it is necessary to make the changes to the listener `src/main/java/org/qubership/cloud/devops/gstringtojinjavatranslator/ParameterTranslator.java`.

All information on the work of the ANTLR grammar and listener is on the website https://www.antlr.org and in the book `The Definitive ANTLR 4 Reference`.

### Additional tools

- [ANTLR v4 Intellij Idea plugin](https://plugins.jetbrains.com/plugin/7358-antlr-v4)
