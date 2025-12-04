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

package org.qubership.cloud.expression;

import static org.hamcrest.CoreMatchers.instanceOf;
import static org.hamcrest.MatcherAssert.assertThat;
import static org.junit.jupiter.api.Assertions.assertEquals;

import org.qubership.cloud.BindingBaseTest;
import org.qubership.cloud.parameters.processor.ParametersProcessor;
import org.qubership.cloud.devops.commons.pojo.parameterset.ParameterSet;
import org.qubership.cloud.devops.commons.pojo.tenants.model.Tenant;
import org.qubership.cloud.devops.commons.pojo.parameterset.ParameterSetApplication;
import org.qubership.cloud.devops.commons.utils.Parameter;
import org.qubership.cloud.parameters.processor.expression.ExpressionLanguage;
import org.qubership.cloud.parameters.processor.expression.binding.Binding;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.MethodSource;
import org.mockito.Mockito;

import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import java.util.stream.Stream;

public class ExpressionLanguageTest extends BindingBaseTest {

    private static Stream<Arguments> processBackslashes() {
        return Stream.of(
                Arguments.of("test", "test"),
                Arguments.of("\\", "\\\\"),
                Arguments.of("${}", "${}"),
                Arguments.of("${\\}", "${\\}"),
                Arguments.of("\\${\\}", "\\\\\\${\\\\}"), // \${\} -> \\\${\\}
                Arguments.of("\\\\$${\\}", "\\\\\\\\$${\\}"),
                Arguments.of("\\}", "\\\\}"),
                Arguments.of("${\\", "${\\")
        );
    }

    private static Stream<Arguments> processValue() {
        return Stream.of(
                Arguments.of(new HashMap<String, Parameter>() {{
                                 put("key1", new Parameter("value1"));
                                 put("key2", new Parameter("value2"));
                             }},
                        new HashMap<String, Parameter>() {{
                            put("key1", new Parameter("value1"));
                            put("key2", new Parameter("value2"));
                        }}),
                Arguments.of(new HashMap<String, Parameter>() {{
                                 put("key1", new Parameter("value1"));
                                 put("key2", new Parameter("$key1"));
                             }},
                        new HashMap<String, Parameter>() {{
                            put("key1", new Parameter("value1"));
                            put("key2", new Parameter("value1"));
                        }}),
                Arguments.of(new HashMap<String, Parameter>() {{
                                 put("key1", new Parameter("value1"));
                                 put("key2", new Parameter("$key1"));
                                 put("key3", new Parameter("$key2"));
                             }},
                        new HashMap<String, Parameter>() {{
                            put("key1", new Parameter("value1"));
                            put("key2", new Parameter("value1"));
                            put("key3", new Parameter("value1"));
                        }}),
                Arguments.of(new HashMap<String, Parameter>() {{
                                 put("key1", new Parameter("value1"));
                                 put("key2", new Parameter("${key1[0..-2]}"));
                             }},
                        new HashMap<String, Parameter>() {{
                            put("key1", new Parameter("value1"));
                            put("key2", new Parameter("value"));
                        }}),
                Arguments.of(new HashMap<String, Parameter>() {{
                                 put("key1", new Parameter("pa\\$\\$word"));
                                 put("key2", new Parameter("$key1"));
                             }},
                        new HashMap<String, Parameter>() {{
                            put("key1", new Parameter("pa$$word"));
                            put("key2", new Parameter("pa$$word"));
                        }}),
                Arguments.of(new HashMap<String, Parameter>() {{
                                 put("key1", new Parameter("\\\\\\$"));
                                 put("key2", new Parameter("\\$"));
                             }},
                        new HashMap<String, Parameter>() {{
                            put("key1", new Parameter("\\$"));
                            put("key2", new Parameter("$"));
                        }})
        );
    }

    private static Stream<Arguments> processMap() {
        return Stream.of(
                Arguments.of(new HashMap<String, Parameter>() {{
                                 put("key", new Parameter("value"));
                             }},
                        new HashMap<String, Parameter>() {{
                            put("key", new Parameter("value"));
                        }}),

                Arguments.of(new HashMap<String, Parameter>() {{
                                 put("key1",
                                         new Parameter(new LinkedList() {{
                                             add("value1");
                                             add("value2");
                                         }}));
                             }},
                        new HashMap<String, Parameter>() {{
                            put("key1",
                                    new Parameter(new LinkedList() {{
                                        add("value1");
                                        add("value2");
                                    }}));
                        }}),

                Arguments.of(new HashMap<String, Parameter>() {{
                                 put("key1",
                                         new Parameter(new LinkedList() {{
                                             add("value1");
                                             add("value2");
                                         }}));
                             }},
                        new HashMap<String, Parameter>() {{
                            put("key1",
                                    new Parameter(new LinkedList() {{
                                        add("value1");
                                        add("value2");
                                    }}));
                        }}),
                Arguments.of(new HashMap<String, Parameter>() {{
                                 put("key", new Parameter("$key2"));
                             }},
                        new HashMap<String, Parameter>() {{
                            put("key", new Parameter("$key2"));
                        }})
        );
    }

    private static Stream<Arguments> processDeployment() {
        return Stream.of(
                Arguments.of(new HashMap<String, Object>(),
                        new HashMap<String, Object>(),
                        new HashMap<String, Object>()),
                Arguments.of(new HashMap<String, Object>() {{
                                 put("key1", "value1");
                                 put("key2", "$key1");
                             }},
                        new HashMap<String, Object>(),
                        new HashMap<String, Object>() {{
                            put("key1", "value1");
                            put("key2", "value1");
                        }}),
                Arguments.of(new HashMap<String, Object>() {{
                                 put("key1", "value1");
                                 put("key2", "${cloud.key1}");
                             }},
                        new HashMap<String, Object>() {{
                            put("key1", "value2");
                        }},
                        new HashMap<String, Object>() {{
                            put("key1", "value2");
                            put("key2", "value2");
                        }}),
                Arguments.of(new HashMap<String, Object>() {{
                                 put("key1", "value1");
                                 put("key2", "${key1}");
                             }},
                        new HashMap<String, Object>() {{
                            put("key1", "value2");
                        }},
                        new HashMap<String, Object>() {{
                            put("key1", "value2");
                            put("key2", "value2");
                        }}),
                Arguments.of(new HashMap<String, Object>() {{
                                 put("key1", "'key: value'");
                                 put("key2", "'{\"key\": [\"value1\", \"value2\"]}'");
                                 put("key3", "'{\"key\": null}'");
                             }},
                        new HashMap<String, Object>() {{
                            put("key2", "'{\"key\": [\"value3\"]}'");
                        }},
                        new HashMap<String, Object>() {{
                            put("key1", new HashMap<String, Object>() {{
                                put("key", "value");
                            }});
                            put("key2", new HashMap<String, Object>() {{
                                put("key", new ArrayList<Object>() {{
                                    add("value1");
                                    add("value2");
                                    add("value3");
                                }});
                            }});
                            put("key3", new HashMap<String, Object>() {{
                                put("key", null);
                            }});
                        }}),
                Arguments.of(new HashMap<String, Object>() {{
                                 put("key1", "value1");
                                 put("key2", "${key3}");
                             }},
                        new HashMap<String, Object>() {{
                            put("key3", "value3");
                        }},
                        new HashMap<String, Object>() {{
                            put("key1", "value1");
                            put("key2", "value3");
                            put("key3", "value3");
                        }}),
                Arguments.of(new HashMap<String, Object>() {{
                                 put("key1", "value1");
                                 put("key2", "${key3}");
                             }},
                        new HashMap<String, Object>() {{
                            put("key3", "null");
                        }},
                        new HashMap<String, Object>() {{
                            put("key1", "value1");
                            put("key2", "null");
                            put("key3", "null");
                        }}),
                Arguments.of(new HashMap<String, Object>() {{
                                 put("key1", "\\$");
                                 put("key2", "\\\\\\$");
                             }},
                        new HashMap<String, Object>(),
                        new HashMap<String, Object>() {{
                            put("key1", "$");
                            put("key2", "\\$");
                        }}),
                Arguments.of(new HashMap<String, Object>() {{
                                 put("key1", "${false ?: 1}");
                             }},
                        new HashMap<String, Object>(),
                        new HashMap<String, Object>() {{
                            put("key1", "1");
                        }}),
                Arguments.of(new HashMap<String, Object>() {{
                                 put("key1", "'[{\"test\": \"value\"}]");
                             }},
                        new HashMap<String, Object>(),
                        new HashMap<String, Object>() {{
                            put("key1", new ArrayList<Object>() {{
                                add(new HashMap<String, Object>() {{
                                    put("test", "value");
                                }});
                            }});
                        }})
        );
    }

    private static Stream<Arguments> processDeployment_deafult_ES_false() {
        return Stream.of(Arguments.of(new HashMap<String, Object>() {{
                                          put("key1", "\"value1\"");
                                      }},
                        new HashMap<String, Object>() {{
                            put("key2", "\"value2\"");
                        }},
                        new HashMap<String, Object>() {{
                            put("key1", "\"value1\"");
                            put("key2", "\"value2\"");
                        }})
        );
    }

    private static Stream<Arguments> processDeployment_with_parameter_sets() {
        return Stream.of(
                Arguments.of(new HashMap<String, Object>(),
                        new LinkedList<String>(),
                        new LinkedList<ParameterSet>() {{
                            add(new ParameterSet(new Tenant("tenant"), "set1",
                                    new HashMap<String, String>() {{
                                        put("SET_PARAM", "value");
                                    }},
                                    Collections.emptyList()));
                        }},
                        new HashMap<String, Object>() {{
                            put("SET_PARAM", "value");
                        }}),
                Arguments.of(new HashMap<String, Object>(),
                        new LinkedList<String>(),
                        new LinkedList<ParameterSet>() {{
                            add(new ParameterSet(new Tenant("tenant"), "set1",
                                    new HashMap<String, String>() {{
                                        put("SET_PARAM", "value1");
                                    }},
                                    new LinkedList<ParameterSetApplication>() {{
                                        add(new ParameterSetApplication("application", new HashMap<String, String>() {
                                            {
                                                put("SET_PARAM", "value2");
                                            }
                                        }));
                                    }}));
                        }},
                        new HashMap<String, Object>() {
                            {
                                put("SET_PARAM", "value2");
                            }
                        }),
                Arguments.of(new HashMap<String, Object>(),
                        new LinkedList<String>(),
                        new LinkedList<ParameterSet>() {{
                            add(new ParameterSet(new Tenant("tenant"), "set1",
                                    new HashMap<String, String>() {{
                                        put("SET_PARAM", "value");
                                    }},
                                    Collections.emptyList()));
                            add(new ParameterSet(new Tenant("tenant"), "set2",
                                    new HashMap<String, String>() {{
                                        put("SET_2_PARAM", "value2");
                                    }},
                                    Collections.emptyList()));
                        }},
                        new HashMap<String, Object>() {{
                            put("SET_PARAM", "value");
                        }}),
                Arguments.of(new HashMap<String, Object>(),
                        new LinkedList<String>() {{
                            add("set2");
                        }},
                        new LinkedList<ParameterSet>() {{
                            add(new ParameterSet(new Tenant("tenant"), "set1",
                                    new HashMap<String, String>() {{
                                        put("SET_PARAM", "value");
                                    }},
                                    Collections.emptyList()));
                            add(new ParameterSet(new Tenant("tenant"), "set2",
                                    new HashMap<String, String>() {{
                                        put("SET_2_PARAM", "value2");
                                    }},
                                    Collections.emptyList()));
                        }},
                        new HashMap<String, Object>() {{
                            put("SET_PARAM", "value");
                            put("SET_2_PARAM", "value2");
                        }}),
                Arguments.of(new HashMap<String, Object>(),
                        new LinkedList<String>() {{
                            add("set2");
                            add("set3");
                        }},
                        new LinkedList<ParameterSet>() {{
                            add(new ParameterSet(new Tenant("tenant"), "set1",
                                    new HashMap<String, String>() {{
                                        put("SET_PARAM", "value");
                                    }},
                                    Collections.emptyList()));
                            add(new ParameterSet(new Tenant("tenant"), "set2",
                                    new HashMap<String, String>() {{
                                        put("SET_2_PARAM", "value2");
                                    }},
                                    Collections.emptyList()));
                            add(new ParameterSet(new Tenant("tenant"), "set3",
                                    new HashMap<String, String>() {{
                                        put("SET_3_PARAM", "value3");
                                    }},
                                    Collections.emptyList()));
                        }},
                        new HashMap<String, Object>() {{
                            put("SET_PARAM", "value");
                            put("SET_2_PARAM", "value2");
                            put("SET_3_PARAM", "value3");
                        }}),
                Arguments.of(new HashMap<String, Object>(),
                        new LinkedList<String>() {{
                            add("set2");
                        }},
                        new LinkedList<ParameterSet>() {{
                            add(new ParameterSet(new Tenant("tenant"), "set1",
                                    new HashMap<String, String>() {{
                                        put("SET_PARAM", "value");
                                    }},
                                    Collections.emptyList()));
                            add(new ParameterSet(new Tenant("tenant"), "set2",
                                    new HashMap<String, String>() {{
                                        put("SET_PARAM", "value2");
                                    }},
                                    Collections.emptyList()));
                        }},
                        new HashMap<String, Object>() {{
                            put("SET_PARAM", "value");
                        }}),
                Arguments.of(new HashMap<String, Object>(),
                        new LinkedList<String>() {{
                            add("set2");
                            add("set3");
                        }},
                        new LinkedList<ParameterSet>() {{
                            add(new ParameterSet(new Tenant("tenant"), "set1",
                                    new HashMap<String, String>() {{
                                        put("SET_PARAM", "value");
                                    }},
                                    Collections.emptyList()));
                            add(new ParameterSet(new Tenant("tenant"), "set2",
                                    new HashMap<String, String>() {{
                                        put("SET_2_PARAM", "value2");
                                    }},
                                    Collections.emptyList()));
                            add(new ParameterSet(new Tenant("tenant"), "set3",
                                    new HashMap<String, String>() {{
                                        put("SET_2_PARAM", "value3");
                                    }},
                                    Collections.emptyList()));
                        }},
                        new HashMap<String, Object>() {{
                            put("SET_PARAM", "value");
                            put("SET_2_PARAM", "value3");
                        }}));
    }

    @ParameterizedTest
    @MethodSource
    public void processBackslashes(String string, String result) throws IllegalAccessException, InvocationTargetException, NoSuchMethodException {
        Binding binding = Mockito.mock(Binding.class);

        ExpressionLanguage el = new ExpressionLanguage(binding);
        Method processBackslashes = ExpressionLanguage.class.getDeclaredMethod("processBackslashes", String.class);
        processBackslashes.setAccessible(true);
        assertEquals(result, processBackslashes.invoke(el, string));
    }

    @ParameterizedTest
    @MethodSource
    public void processValue(Map<String, Parameter> params, Map<String, Parameter> result) throws IllegalAccessException, InvocationTargetException, NoSuchMethodException {
        Binding binding = new Binding("true");
        binding.putAll(params);

        ExpressionLanguage el = new ExpressionLanguage(binding);
        Method processValue = ExpressionLanguage.class.getDeclaredMethod("processValue", Object.class);
        processValue.setAccessible(true);

        for (Map.Entry<String, Parameter> it : result.entrySet()) {
            assertEquals(it.getValue(), processValue.invoke(el, params.get(it.getKey())));
        }
    }

    @ParameterizedTest
    @MethodSource
    public void processMap(Map<String, Parameter> map, Map<String, Parameter> result) throws IllegalAccessException, InvocationTargetException, NoSuchMethodException {
        Binding binding = Mockito.mock(Binding.class);

        ExpressionLanguage el = new ExpressionLanguage(binding);
        Method processMap = ExpressionLanguage.class.getDeclaredMethod("processMap", Map.class);
        processMap.setAccessible(true);
        assertEquals(result, processMap.invoke(el, map));
    }

    @ParameterizedTest
    @MethodSource
    public void processDeployment(Map<String, Object> tenant, Map<String, Object> cloud, Map<String, Object> result) {
        Binding binding = setupBinding(new HashMap() {{
            put("tenantParams", tenant);
            put("cloudParams", cloud);
            put("defaultEscapeSequence", "true");
        }});
        Map<String, Object> map = ParametersProcessor.convertParameterMapToObject(new ExpressionLanguage(binding).processDeployment());
        map.remove("MAAS_ENABLED");
        map.remove("VAULT_INTEGRATION");
        map.remove("NAMESPACE");
        map.remove("CLOUDNAME");
        map.remove("TENANTNAME");
        map.remove("APPLICATION_NAME");
        map.remove("PRODUCTION_MODE");
        map.remove("CLOUD_API_HOST");
        map.remove("CLOUD_PUBLIC_HOST");
        map.remove("CLOUD_PRIVATE_HOST");
        map.remove("CLOUD_PROTOCOL");
        map.remove("SERVER_HOSTNAME");
        map.remove("CUSTOM_HOST");
        map.remove("OPENSHIFT_SERVER");
        map.remove("CLOUD_API_PORT");
        assertEquals(result, map);
    }

    @ParameterizedTest
    @MethodSource
    public void processDeployment_deafult_ES_false(Map<String, Object> tenant, Map<String, Object> cloud, Map<String, Object> result) {
        tenant.put("ESCAPE_SEQUENCE", "true");
        Binding binding = setupBinding(new HashMap() {{
            put("tenantParams", tenant);
            put("cloudParams", cloud);
            put("defaultEscapeSequence", "false");
        }});
        Map<String, Object> map = ParametersProcessor.convertParameterMapToObject(new ExpressionLanguage(binding).processDeployment());
        map.remove("MAAS_ENABLED");
        map.remove("VAULT_INTEGRATION");
        map.remove("NAMESPACE");
        map.remove("CLOUDNAME");
        map.remove("TENANTNAME");
        map.remove("APPLICATION_NAME");
        map.remove("PRODUCTION_MODE");
        map.remove("CLOUD_API_HOST");
        map.remove("CLOUD_PUBLIC_HOST");
        map.remove("CLOUD_PRIVATE_HOST");
        map.remove("CLOUD_PROTOCOL");
        map.remove("SERVER_HOSTNAME");
        map.remove("CUSTOM_HOST");
        map.remove("OPENSHIFT_SERVER");
        map.remove("CLOUD_API_PORT");

        result.put("ESCAPE_SEQUENCE", "true");
        assertEquals(result, map);
    }

    @Test
    public void processDeployment_check_return_value_is_not_Parameter() {
        Binding binding = setupBinding(new HashMap() {
            {
                put("tenantParams", Collections.singletonMap("struct", "'[{\"map\":{}, \"list\": []}]'"));
                put("defaultEscapeSequence", "true");
            }
        });
        Map<String, Object> map = ParametersProcessor.convertParameterMapToObject(new ExpressionLanguage(binding).processDeployment());
        map.remove("MAAS_ENABLED");
        map.remove("VAULT_INTEGRATION");

        assertThat(map.get("struct"), instanceOf(List.class));
        assertThat(((List) map.get("struct")).get(0), instanceOf(Map.class));
        assertThat(((Map) ((List) map.get("struct")).get(0)).get("map"), instanceOf(Map.class));
        assertThat(((Map) ((List) map.get("struct")).get(0)).get("list"), instanceOf(List.class));
    }

    @Test
    void processedGlobalResourceProfileMustBeSuccessfullyProcessedAgain() throws NoSuchMethodException, InvocationTargetException, IllegalAccessException {
        Binding binding = new Binding("true");
        binding.setDefault("");
        HashMap<String, Object> map = new HashMap<>(){{
            put("key1", "value1");
            put("key2", "value2");
        }};
        Parameter parameter = new Parameter(map);
        parameter.setParsed(true);
        parameter.setValid(true);
        parameter.setProcessed(true);
        parameter.setOrigin("Params/Namespace: GRP_TEST");
        binding.put("GLOBAL_RESOURCE_PROFILE", parameter);

        ExpressionLanguage el = new ExpressionLanguage(binding);
        Method processMap = ExpressionLanguage.class.getDeclaredMethod("processMap", Map.class, Map.class, boolean.class);
        processMap.setAccessible(true);
        assertEquals("{GLOBAL_RESOURCE_PROFILE={key1=value1, key2=value2}}", processMap.invoke(el, binding, binding, true).toString());
    }
    @Test
    void testTypePreservation_IntegerType() throws NoSuchMethodException, InvocationTargetException, IllegalAccessException {
        Binding binding = new Binding("true");
        binding.put("MONGO_DB_PORT", new Parameter(27017));
        binding.put("DUMPS_MONGO_PORT", new Parameter("${MONGO_DB_PORT}"));

        ExpressionLanguage el = new ExpressionLanguage(binding);
        Method processValue = ExpressionLanguage.class.getDeclaredMethod("processValue", Object.class);
        processValue.setAccessible(true);
        Parameter result = (Parameter) processValue.invoke(el, binding.get("DUMPS_MONGO_PORT"));

        assertThat(result.getValue(), instanceOf(Integer.class));
        assertEquals(27017, result.getValue());
    }

    @Test
    void testTypePreservation_ConcatenatedExpressionProducesString() throws NoSuchMethodException, InvocationTargetException, IllegalAccessException {
        Binding binding = new Binding("true");
        binding.put("PORT", new Parameter(8080));
        binding.put("PORT_STRING", new Parameter("${PORT}_suffix"));

        ExpressionLanguage el = new ExpressionLanguage(binding);
        Method processValue = ExpressionLanguage.class.getDeclaredMethod("processValue", Object.class);
        processValue.setAccessible(true);
        Parameter result = (Parameter) processValue.invoke(el, binding.get("PORT_STRING"));

        assertThat(result.getValue(), instanceOf(String.class));
        assertEquals("8080_suffix", result.getValue());
    }

    @Test
    void testTypePreservation_IntegerReference() {
        Map<String, Object> tenantParams = new HashMap<String, Object>() {{
            put("MONGO_DB_PORT", 27017);
            put("DUMPS_MONGO_PORT", "${MONGO_DB_PORT}");
        }};

        Binding binding = setupBinding(new HashMap() {{
            put("tenantParams", tenantParams);
            put("cloudParams", new HashMap<>());
            put("defaultEscapeSequence", "true");
        }});

        Map<String, Object> result = ParametersProcessor.convertParameterMapToObject(
                new ExpressionLanguage(binding).processDeployment());

        assertThat(result.get("MONGO_DB_PORT"), instanceOf(Integer.class));
        assertThat(result.get("DUMPS_MONGO_PORT"), instanceOf(Integer.class));
        assertEquals(27017, result.get("DUMPS_MONGO_PORT"));
    }

    @Test
    void testTypePreservation_LongReference() {
        Map<String, Object> tenantParams = new HashMap<String, Object>() {{
            put("CDC_TOPIC_STREAMING_RETENTION_MS", 604800000L);
            put("CDC_TOPIC_REFILL_RETENTION_MS", "${CDC_TOPIC_STREAMING_RETENTION_MS}");
        }};

        Binding binding = setupBinding(new HashMap() {{
            put("tenantParams", tenantParams);
            put("cloudParams", new HashMap<>());
            put("defaultEscapeSequence", "true");
        }});

        Map<String, Object> result = ParametersProcessor.convertParameterMapToObject(
                new ExpressionLanguage(binding).processDeployment());

        assertThat(result.get("CDC_TOPIC_STREAMING_RETENTION_MS"), instanceOf(Long.class));
        assertThat(result.get("CDC_TOPIC_REFILL_RETENTION_MS"), instanceOf(Long.class));
        assertEquals(604800000L, result.get("CDC_TOPIC_REFILL_RETENTION_MS"));
    }

    @Test
    void testTypePreservation_MultipleTypes() {
        Map<String, Object> tenantParams = new HashMap<String, Object>() {{
            put("MONGO_DB_PORT", 27017);
            put("DUMPS_MONGO_PORT", "${MONGO_DB_PORT}");
            put("CDC_TOPIC_STREAMING_RETENTION_MS", 604800000L);
            put("CDC_TOPIC_REFILL_RETENTION_MS", "${CDC_TOPIC_STREAMING_RETENTION_MS}");
            put("CDC_TOPIC_STREAMING_RETENTION_BYTES", 1073741824L);
            put("CDC_TOPIC_REFILL_RETENTION_BYTES", "${CDC_TOPIC_STREAMING_RETENTION_BYTES}");
        }};

        Binding binding = setupBinding(new HashMap() {{
            put("tenantParams", tenantParams);
            put("cloudParams", new HashMap<>());
            put("defaultEscapeSequence", "true");
        }});

        Map<String, Object> result = ParametersProcessor.convertParameterMapToObject(
                new ExpressionLanguage(binding).processDeployment());

        assertThat(result.get("DUMPS_MONGO_PORT"), instanceOf(Integer.class));
        assertEquals(27017, result.get("DUMPS_MONGO_PORT"));

        assertThat(result.get("CDC_TOPIC_REFILL_RETENTION_MS"), instanceOf(Long.class));
        assertEquals(604800000L, result.get("CDC_TOPIC_REFILL_RETENTION_MS"));

        assertThat(result.get("CDC_TOPIC_REFILL_RETENTION_BYTES"), instanceOf(Long.class));
        assertEquals(1073741824L, result.get("CDC_TOPIC_REFILL_RETENTION_BYTES"));
    }
}
