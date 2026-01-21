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

package org.qubership.cloud.parameters.processor.parser;

import org.qubership.cloud.devops.commons.utils.constant.ParametersConstants;
import org.qubership.cloud.devops.commons.utils.Parameter;

import groovy.json.JsonSlurperClassic;
import org.yaml.snakeyaml.Yaml;

import java.io.Serializable;
import java.util.HashMap;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class EscapeParametersParser implements ParametersParser, Serializable {

    private List<String> semicolonSplit(String str) {
        List<String> result = new LinkedList<>();

        Pattern pattern = Pattern.compile("(?<!\\\\)(\\\\\\\\)*(;)");
        Matcher regex = pattern.matcher(str);
        int start = 0, end;
        while (regex.find()) {
            end = regex.end();
            result.add(str.substring(start, end - 1).replaceAll("\\\\;", ";"));

            start = end;
        }
        if (start != str.length()) {
            String last = str.substring(start).replaceAll("\\\\;", ";");
            if (!last.trim().isEmpty()) {
                result.add(last);
            }
        }
        return result;
    }


    @Override
    public Object processParam(String param) {
        param = param.trim();
        String valueOfParam = param.replaceAll("\\\\(['=])", "$1");
        if (!param.isEmpty() && param.charAt(0) == '\'') {
            int len = valueOfParam.length();
            int end = valueOfParam.charAt(len - 1) == '\'' ? len - 1 : len;
            String structuredString = valueOfParam.substring(1, end);
            if (structuredString.isEmpty()) {
                return structuredString;
            }
            if (structuredString.charAt(0) == '{' || structuredString.charAt(0) == '[') {
                try {
                    return new JsonSlurperClassic().parseText(structuredString);
                } catch (groovy.json.JsonException e) {
                    throw new IllegalArgumentException(param + "is invalid. Please check JSON syntax", e);
                }
            } else {
                try {
                    return new Yaml().load(structuredString);
                } catch (org.yaml.snakeyaml.error.YAMLException e) {
                    throw new IllegalArgumentException(param + "is invalid. Please check YAML syntax", e);
                }
            }
        } else {
            return valueOfParam;
        }
    }

    private LineDTO processLine(String paramLine) {
        paramLine = paramLine.trim();
        if (!paramLine.isEmpty()) {
            String[] pairs = paramLine.split("(?<!\\\\)=", 2);
            if (!paramLine.contains("=") || pairs[0].isEmpty()) {
                throw new IllegalArgumentException(
                        "For CUSTOM_PARAMS line " + paramLine + " can not be parsed. This field should contain only lines like PARAM1=VALUE1");
            }

            return new LineDTO(pairs[0].trim(), processParam(pairs[1]));
        }
        return null;
    }

    @Override
    public Map<String, Parameter> parse(String customParams) {
        Map<String, Parameter> result = new HashMap<>();

        semicolonSplit(customParams).forEach(paramLine -> {
            LineDTO line = processLine(paramLine);
            if (line != null) {
                result.put(line.key, new Parameter(line.value, ParametersConstants.CUSTOM_PARAMS_ORIGIN, true));
            }
        });
        return result;
    }

    private static class LineDTO {
        String key;
        Object value;

        LineDTO(String key, Object value) {
            this.key = key;
            this.value = value;
        }
    }
}
