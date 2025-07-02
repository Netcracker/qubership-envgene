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
import org.qubership.cloud.devops.commons.utils.Parameter;
import org.qubership.cloud.parameters.processor.ParametersProcessor;
import org.qubership.cloud.parameters.processor.expression.PlainLanguage;
import org.qubership.cloud.parameters.processor.expression.binding.Binding;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.MethodSource;

import java.util.Collections;
import java.util.HashMap;
import java.util.LinkedList;
import java.util.Map;
import java.util.stream.Stream;

class PlainLanguageTest extends BindingBaseTest {
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
                            put("key2", "$key1");
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
                            put("key2", "${cloud.key1}");
                        }}),
                Arguments.of(new HashMap<String, Object>() {{
                                 put("key1", "'{\"key\": \"value\"}'");
                                 put("key2", "'{\"key\": [\"value1\", \"value2\"]}'");
                             }},
                        new HashMap<String, Object>() {{
                            put("key2", "'{\"key\": [\"value3\"]}'");
                        }},
                        new HashMap<String, Object>() {{
                            put("key1", new HashMap<String, Object>() {{
                                put("key", "value");
                            }});
                            put("key2", new HashMap<String, Object>() {{
                                put("key", new LinkedList<Object>() {{
                                    add("value3");
                                }});
                            }});
                        }}),
                Arguments.of(new HashMap<String, Object>() {{
                                 put("key1", "\"value1\"");
                             }},
                        new HashMap<String, Object>() {{
                            put("key2", "\"value2\"");
                        }},
                        new HashMap<String, Object>() {{
                            put("key1", "\\\"value1\\\"");
                            put("key2", "\\\"value2\\\"");
                        }})
        );
    }


    @ParameterizedTest
    @MethodSource
    void processDeployment(Map<String, Object> tenant, Map<String, Object> cloud, Map<String, Object> result) {
        Binding binding = setupBinding(new HashMap() {{
            put("tenantParams", tenant);
            put("cloudParams", cloud);
            put("defaultEscapeSequence", "false");
        }});
        Map<String, Object> map = ParametersProcessor.convertParameterMapToObject(new PlainLanguage(binding).processDeployment());
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

    @Test
    void processE2E_check_return_value_is_not_Parameter() {
        Binding binding = setupBinding(new HashMap() {
            {
                put("tenantParamsE2E", Collections.singletonMap("struct", "str"));
                put("defaultEscapeSequence", "false");
            }
        });
        Map<String, Parameter> map = new PlainLanguage(binding).processE2E();
        map.remove("MAAS_ENABLED");
        map.remove("VAULT_INTEGRATION");

        assertThat(map.get("struct"), instanceOf(Parameter.class));
    }
}
