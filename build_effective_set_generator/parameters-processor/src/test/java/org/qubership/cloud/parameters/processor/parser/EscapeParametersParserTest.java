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

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import org.qubership.cloud.devops.commons.utils.Parameter;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.MethodSource;

import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.util.HashMap;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import java.util.stream.Stream;

public class EscapeParametersParserTest {
    private static EscapeParametersParser parser = new EscapeParametersParser();

    private static Stream<Arguments> semicolonSplit() {
        return Stream.of(
                Arguments.of("key=value;", new LinkedList<String>() {{
                    add("key=value");
                }}),
                Arguments.of("key=value", new LinkedList<String>() {{
                    add("key=value");
                }}),
                Arguments.of("key=value; ", new LinkedList<String>() {{
                    add("key=value");
                }}),
                Arguments.of("key1=value1;key2=value2", new LinkedList<String>() {{
                    add("key1=value1");
                    add("key2=value2");
                }}),
                Arguments.of("key1=value1;key2=value2;", new LinkedList<String>() {{
                    add("key1=value1");
                    add("key2=value2");
                }}),
                Arguments.of("key1=value1\\;key2=value2", new LinkedList<String>() {{
                    add("key1=value1;key2=value2");
                }}),
                Arguments.of("key1=value1\\\\;key2=value2", new LinkedList<String>() {{
                    add("key1=value1\\\\");
                    add("key2=value2");
                }}),
                Arguments.of("key1=value1\\\\\\;key2=value2", new LinkedList<String>() {{
                    add("key1=value1\\\\;key2=value2");
                }}),
                Arguments.of("key1=value1\\\\\\\\;key2=value2", new LinkedList<String>() {{
                    add("key1=value1\\\\\\\\");
                    add("key2=value2");
                }})
        );
    }

    private static Stream<Arguments> processParam() {
        return Stream.of(
                //String
                Arguments.of("value", "value"),
                Arguments.of("\\'value\\'", "'value'"),
                Arguments.of("\\'value'", "'value'"),
                Arguments.of("\\\\'value\\'", "\\'value'"),
                Arguments.of("\"value\"", "\"value\""),
                Arguments.of("''", ""),
                Arguments.of("'value' ", "value"),
                Arguments.of("value ", "value"),
                //JSON
                Arguments.of("'{\"key\":\"value\"}'", new HashMap<String, Object>() {{
                    put("key", "value");
                }}),
                Arguments.of("' {\"key\":\"value\"}'", new HashMap<String, Object>() {{
                    put("key", "value");
                }}),
                Arguments.of("'{\"key\":\"value\\\\\"}'", new HashMap<String, Object>() {{
                    put("key", "value\\");
                }}),
                Arguments.of("'{\"key\":\"\\\"value\\\"\"}'", new HashMap<String, Object>() {{
                    put("key", "\"value\"");
                }}),
                Arguments.of("'[\"value1\", \"value2\"]'", new LinkedList<String>() {{
                    add("value1");
                    add("value2");
                }}),
                Arguments.of("'{\"key\": [\"value1\", \"value2\"]}'", new HashMap<String, Object>() {{
                    put("key", new LinkedList<String>() {{
                        add("value1");
                        add("value2");
                    }});
                }}),
                //YAML
                Arguments.of("'key: value'", new HashMap<String, Object>() {{
                    put("key", "value");
                }}),
                Arguments.of("'key: value", new HashMap<String, Object>() {{
                    put("key", "value");
                }}),
                Arguments.of("'  key1: value1\n  key2: value2'", new HashMap<String, Object>() {{
                    put("key1", "value1");
                    put("key2", "value2");
                }}),
                Arguments.of("'key: value\\\\'", new HashMap<String, Object>() {{
                    put("key", "value\\");
                }}),
                Arguments.of("'key: '\"value\"''", new HashMap<String, Object>() {{
                    put("key", "\"value\"");
                }}),
                Arguments.of("'- value1\n- value2'", new LinkedList<String>() {{
                    add("value1");
                    add("value2");
                }}),
                Arguments.of("'key:\n- value1\n- value2'", new HashMap<String, Object>() {{
                    put("key", new LinkedList<String>() {{
                        add("value1");
                        add("value2");
                    }});
                }})

        );
    }

    private static Stream<Arguments> parse() {
        return Stream.of(
                Arguments.of("key=value;", new HashMap() {{
                    put("key", new Parameter("value"));
                }}),
                Arguments.of("key=;", new HashMap() {{
                    put("key", new Parameter(""));
                }}),
                Arguments.of("", new HashMap()),
                Arguments.of("key=va\\nlue", new HashMap() {{
                    put("key", new Parameter("va\\nlue"));
                }}),
                Arguments.of("key1=value1; key2=value2;", new HashMap() {{
                    put("key1", new Parameter("value1"));
                    put("key2", new Parameter("value2"));
                }})

        );
    }

    @ParameterizedTest
    @MethodSource
    public void semicolonSplit(String string, List<String> result) throws IllegalAccessException, InvocationTargetException, NoSuchMethodException {
        Method semicolonSplit = EscapeParametersParser.class.getDeclaredMethod("semicolonSplit", String.class);
        semicolonSplit.setAccessible(true);
        assertEquals(result, semicolonSplit.invoke(parser, string));
    }

    @ParameterizedTest
    @MethodSource
    public void processParam(String string, Object result) {
        assertEquals(result, parser.processParam(string));
    }

    @ParameterizedTest
    @MethodSource
    public void parse(String string, Map<String, Object> result) {
        assertEquals(result, parser.parse(string));
    }

    @Test
    public void parse_without_equal_sign() {
        assertThrows(IllegalArgumentException.class, () -> parser.parse("key:value"));
    }

    @Test
    public void parse_empty_key() {
        assertThrows(IllegalArgumentException.class, () -> parser.parse("=value"));
    }

    @Test
    public void parse_without_invalid_JSON() {
        assertThrows(IllegalArgumentException.class, () -> parser.parse("key='[\"key\":\"value\"]'"));
    }

    @Test
    public void parse_without_invalid_YAML() {
        assertThrows(IllegalArgumentException.class, () -> parser.parse("key='key1:\nkey2'"));
    }
}
