/*
 * Copyright 2024-2025 NetCracker Technology Corporation
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package org.qubership.cloud.parameters.processor.expression;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.github.benmanes.caffeine.cache.Caffeine;
import com.github.benmanes.caffeine.cache.LoadingCache;
import com.hubspot.jinjava.Jinjava;
import com.hubspot.jinjava.JinjavaConfig;
import com.hubspot.jinjava.interpret.FatalTemplateErrorsException;
import groovy.lang.GroovyClassLoader;
import groovy.lang.GroovyRuntimeException;
import groovy.text.GStringTemplateEngine;
import groovy.text.StreamingTemplateEngine;
import groovy.text.Template;
import groovy.text.TemplateEngine;
import lombok.extern.slf4j.Slf4j;
import org.qubership.cloud.devops.commons.utils.Parameter;
import org.qubership.cloud.devops.commons.utils.constant.ParametersConstants;
import org.qubership.cloud.devops.gstringtojinjavatranslator.jinjava.*;
import org.qubership.cloud.devops.gstringtojinjavatranslator.translator.GStringToJinJavaTranslator;
import org.qubership.cloud.parameters.processor.MergeMap;
import org.qubership.cloud.parameters.processor.ParametersProcessor;
import org.qubership.cloud.parameters.processor.exceptions.ExpressionLanguageException;
import org.qubership.cloud.parameters.processor.expression.binding.Binding;
import org.qubership.cloud.parameters.processor.expression.binding.DynamicMap;
import org.qubership.cloud.parameters.processor.expression.binding.DynamicPropertyResolver;
import org.qubership.cloud.parameters.processor.expression.binding.EscapeMap;
import org.qubership.cloud.parameters.processor.expression.interpreter.ParameterUnwrapped;

import java.io.IOException;
import java.time.Duration;
import java.util.*;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Collectors;


@Slf4j
public class ExpressionLanguage extends AbstractLanguage {

    private static final Pattern EXPRESSION_PATTERN = Pattern.compile("(?<!\\\\)(\\\\\\\\)*(\\$)");
    private static final Pattern SECURED_PATTERN = Pattern.compile("(?:\\u0096)(?s)(.+)(?:\\u0097)");
    private final ObjectMapper mapper = new ObjectMapper();
    private boolean insecure;

    private final Jinjava jinjava;
    private final GStringToJinJavaTranslator gStringToJinJavaTranslator;

    public ExpressionLanguage(Binding binding) {
        super(binding);

        JinjavaConfig config = JinjavaConfig.newBuilder()
                .withTokenScannerSymbols(new LessThanTokenScannerSymbols())
                .withObjectUnwrapper(new ParameterUnwrapped())
                .withFailOnUnknownTokens(true)
                .build();
        this.jinjava = new CustomJinjava(config);
        setUpJinJava();

        this.insecure = true;
        this.gStringToJinJavaTranslator = new GStringToJinJavaTranslator();

        this.binding.forEach((key1, value) ->
                this.binding.put(key1, translateParameter(value.getValue())));
    }

    private Parameter translateParameter(Object value) {
        Object val = getValue(value);

        if (val instanceof String) {
            String strVal = (String) val;
            strVal = strVal.replaceAll("\\\\\"", "\"");

            if (value instanceof Parameter) {
                Parameter oldParameter = (Parameter) value;
                return new Parameter(
                        strVal,
                        oldParameter.getOrigin(),
                        oldParameter.isParsed(),
                        oldParameter.isSecured(),
                        gStringToJinJavaTranslator.translate(strVal));
            } else {
                return new Parameter(
                        strVal,
                        gStringToJinJavaTranslator.translate(strVal));
            }
        } else if (val instanceof List) {
            return translateList((List) val);
        } else if (val instanceof Map) {
            return translateMap((Map) val);
        }

        if (value instanceof Parameter) {
            return (Parameter) value;
        }

        return new Parameter(value);
    }

    private Parameter translateMap(Map<String, Object> map) {
        map.replaceAll((k, v) -> translateParameter(v));
        return new Parameter(map);
    }

    private Parameter translateList(List<Object> list) {
        for (final ListIterator<Object> it = list.listIterator(); it.hasNext(); ) {
            Object element = it.next();
            it.set(translateParameter(element));
        }
        return new Parameter(list);
    }

    private void setUpJinJava() {
        this.jinjava.registerFilter(new EnvSuffixFilter());
        this.jinjava.registerFilter(new EnvPrefixFilter());
        this.jinjava.registerFunction(Functions.randomFunction());
        this.jinjava.getGlobalContext().setDynamicVariableResolver(new DynamicPropertyResolver(binding));
    }

    /*
        Escape backslashes that are not inside macros ${}
    */
    private static String processBackslashes(String str) {
        StringBuilder builder = new StringBuilder();
        int bsCount = 0;
        boolean dollar = false;
        boolean closure = false;
        for (int i = 0; i < str.length(); i++) {
            char ch = str.charAt(i);
            switch (ch) {
                case '\\':
                    builder.append(ch);
                    if (!closure) {
                        builder.append(ch);
                    }
                    bsCount++;
                    continue;
                case '$':
                    if (bsCount % 2 != 0) {
                        builder.append('\\');
                    } else {
                        dollar = true;
                    }
                    bsCount = 0;
                    builder.append(ch);
                    continue;
                case '{':
                case '<':
                    if (dollar) {
                        closure = true;
                    }
                    break;
                case '}':
                case '>':
                    if (closure && bsCount % 2 == 0) {
                        closure = false;
                    }
                    break;
            }
            dollar = false;
            bsCount = 0;
            builder.append(ch);

        }
        return builder.toString();
    }

    @Override
    protected Map<String, Parameter> createMap() {
        return new MergeMap();
    }

    private Object getValue(Object object) {
        if (object instanceof Parameter) {
            return ((Parameter) object).getValue();
        } else {
            return object;
        }
    }

    private boolean getIsSecured(Object object) {
        if (object instanceof Parameter) {
            return ((Parameter) object).isSecured();
        } else {
            return false;
        }
    }

    private Parameter processValue(Object value, Map<String, Parameter> binding, boolean escapeDollar)
            throws IOException {
        if (value instanceof Parameter && ((Parameter) value).isProcessed()) {
            Parameter parameter = (Parameter) value;
            parameter.setValue(removeEscaping(escapeDollar, parameter.getValue()));
            return parameter;
        }
        Object val = getValue(value);
        boolean isProcessed = false;
        boolean isSecured = getIsSecured(value);

        if (val instanceof String) {
            String strValue = (String) val;


            String jinJavaRendered = "";
            try {
                jinJavaRendered = renderStringByJinJava(strValue, binding, escapeDollar);
                val = jinJavaRendered;
            } catch (Exception e) {
                log.debug(String.format("Parameter {} was not processed by JinJava, hence reverting to Groovy.", strValue));
                String groovyRendered = renderStringByGroovy(strValue, binding, escapeDollar);
                val = groovyRendered;
            }

            isProcessed = true;

            Matcher secureMarkerMatcher = SECURED_PATTERN.matcher((String) val);
            if (secureMarkerMatcher.find()) {
                isSecured = true;
                val = ((String) Objects.requireNonNull(val)).replaceAll("([\\u0096\\u0097])", "");
            }
        } else if (val instanceof List) {
            val = processList((List<Parameter>) val, binding, escapeDollar);
        } else if (val instanceof Map) {
            val = processMap((Map<String, Parameter>) val, binding, escapeDollar);
        }
        Parameter ret = new Parameter(value);
        ret.setValue(val);
        ret.setProcessed(isProcessed);
        ret.setSecured(isSecured);
        return ret;
    }

    private String renderStringByGroovy(String value, Map<String, Parameter> binding, boolean escapeDollar) {
        int i = 0;
        String rendered = value;
        while (EXPRESSION_PATTERN.matcher(rendered).find()) {
            if (i++ > 50) {
                throw new ExpressionLanguageException("Too much nesting in value " + value + ". It may be result of recursive transitive expressions.");
            }

            rendered = TemplateProvider.get(rendered).make(binding).toString();
        }

        if (escapeDollar) {
            rendered = rendered.replaceAll("\\\\\\$", "\\$"); // \$ -> $
            rendered = rendered.replaceAll("\\\\\\\\", "\\\\"); // \\ -> \
        }
        return rendered;
    }

    private String renderStringByJinJava(String value, Map<String, Parameter> binding, boolean escapeDollar) {
        String rendered = gStringToJinJavaTranslator.translate(value);
        rendered = jinjava.render(rendered, binding);

        if (escapeDollar) {
            rendered = rendered.replaceAll("\\\\\\$", "\\$"); // \$ -> $
            rendered = rendered.replaceAll("\\\\\\\\", "\\\\"); // \\ -> \
        }

        return rendered;
    }

    private Object removeEscaping(boolean escapeDollar, Object val) throws JsonProcessingException {
        if (escapeDollar && val != null) {
            String strValue;
            if (val instanceof String) {
                strValue = val.toString();
            } else {
                strValue = mapper.writeValueAsString(val);
            }
            strValue = strValue.replaceAll("\\\\\\$", "\\$"); // \$ -> $
            val = strValue.replaceAll("\\\\\\\\", "\\\\"); // \\ -> \
        }
        return val;
    }

    private List<Parameter> processList(List<?> list, Map<String, Parameter> binding, boolean escapeDollar) {
        return list.stream().map(entry -> {
            try {
                return processValue(entry, binding, escapeDollar);
            } catch (IOException | GroovyRuntimeException | FatalTemplateErrorsException e) {
                if (insecure) {
                    return new Parameter(entry);
                } else {
                    throw new ExpressionLanguageException("Could not process expression " + entry + ". " + e.getMessage());
                }
            }
        }).collect(Collectors.toList());
    }

    protected Map<String, Parameter> processMap(Map<String, Parameter> map) {
        return processMap(map, this.binding, false);
    }

    private AbstractMap.SimpleEntry<String, ?> failedParameter(Map.Entry<String, ?> entry) {
        Parameter parameter = new Parameter(entry.getValue());
        parameter.setValid(false);
        return new AbstractMap.SimpleEntry<>(entry.getKey(), parameter);
    }

    private Map<String, Parameter> processMap(Map<String, ?> map, Map<String, Parameter> binding, boolean escapeDollar) {
        if (map == null) {
            map = Collections.emptyMap();
        }

        return map.entrySet().stream()
                .filter(x -> getValue(x.getValue()) instanceof String || !(getValue(x.getValue()) instanceof DynamicMap || getValue(x.getValue()) instanceof EscapeMap))
                .map(entry -> {
                    try {
                        Parameter processedValue = processValue(entry.getValue(), binding, escapeDollar);
                        if (entry.getKey().equals(ParametersConstants.GLOBAL_RESOURCE_PROFILE) && processedValue.getValue() instanceof String) {
                            processedValue.setValue(super.binding.getParser().processParam("'" + processedValue.getValue() + "'"));
                        }
                        if (insecure && (processedValue.getValue() == null || processedValue.getValue().equals("null"))) {
                            return failedParameter(entry);
                        }
                        return new AbstractMap.SimpleEntry<>(entry.getKey(), processedValue);
                    } catch (IOException | GroovyRuntimeException |
                             ArrayIndexOutOfBoundsException | FatalTemplateErrorsException e) {
                        if (insecure) {
                            return failedParameter(entry);
                        } else {
                            throw new ExpressionLanguageException(String.format("Could not process expression for parameter %s with value: %s", entry.getKey(), entry.getValue()), e);
                        }
                    }
                }).collect(HashMap::new, (m, entry) -> m.put(entry.getKey(), new Parameter(entry.getValue())), HashMap::putAll);
    }

    protected Map<String, Parameter> processMap(String mapName) {
        return processMap(binding.setDefault(mapName));
    }

    @Override
    public Map<String, Parameter> processDeployment() {
        Map<String, Parameter> result = new MergeMap();

        processNamespaceApp(result);
        result.putAll(processMap(""));


        insecure = false;
        return processMap(result, result, true);
    }

    @Override
    public Map<String, Parameter> processE2E() {
        Map<String, Parameter> result = new MergeMap();

        processE2E(result);
        insecure = false;
        return processMap(result, result, true);
    }

    @Override
    public Map<String, Parameter> processCloudE2E() {
        Map<String, Parameter> result = new MergeMap();

        processCloudE2E(result);
        insecure = false;
        return processMap(result, result, true);
    }

    @Override
    public Map<String, Parameter> processNamespaceApp() {
        Map<String, Parameter> result = new MergeMap();

        processNamespaceApp(result);

        return processMap(result, result, true);
    }

    @Override
    public Map<String, Parameter> processNamespace() {
        Map<String, Parameter> result = new MergeMap();

        processNamespace(result);

        return processMap(result, result, true);
    }

    @Override
    public Map<String, Parameter> processConfigServerApp() {
        return processConfigServerAppsInternal();
    }

    public Map<String, Parameter> processConfigServerAppsInternal() {
        Map<String, Parameter> result = new MergeMap();

        processNamespaceAppConfigServer(result);
        insecure = false;
        return processMap(result, result, true);
    }

    @Override
    public Map<String, Parameter> processNamespaceAppConfigServer() {
        Map<String, Parameter> result = new MergeMap();

        processNamespaceAppConfigServer(result);
        return processMap(result, result, true);
    }

    private static class TemplateProvider {
        private static final TemplateEngine ENGINE = createEngine("GString");
        private static final LoadingCache<String, Template> TEMPLATES = createCache(1000, Duration.ofMinutes(10));

        public static LoadingCache<String, Template> createCache(Integer cacheSize, Duration expire) {
            return Caffeine.newBuilder()
                    .maximumSize(cacheSize)
                    .expireAfterAccess(expire)
                    .recordStats()
                    .build(key -> {
                        try {
                            return ENGINE.createTemplate(processBackslashes(key));
                        } catch (ClassNotFoundException | IOException e) {
                            throw new ExpressionLanguageException("Can not create template for " + key, e);
                        }
                    });
        }

        public static TemplateEngine createEngine(String type) {
            switch (type) {
                case "GString":
                    return new GStringTemplateEngine(new GroovyClassLoader(TemplateProvider.class.getClassLoader()));
                case "Streaming":
                    return new StreamingTemplateEngine(new GroovyClassLoader(TemplateProvider.class.getClassLoader()));
            }
            return null;
        }


        public static Template get(String val) {
            return TEMPLATES.get(val);
        }
    }

    @SuppressWarnings("unsed")
    /* This method are used from reflection*/
    private Parameter processValue(Object value) throws IOException {
        return processValue(value, this.binding, true);
    }
}