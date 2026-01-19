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

import static org.junit.Assert.assertThrows;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.qubership.cloud.BindingBaseTest;
import org.qubership.cloud.parameters.processor.ParametersProcessor;
import org.qubership.cloud.parameters.processor.exceptions.ExpressionLanguageException;
import org.qubership.cloud.parameters.processor.expression.ExpressionLanguage;
import org.qubership.cloud.parameters.processor.expression.binding.Binding;

import org.junit.jupiter.api.Test;

import java.io.Serializable;
import java.lang.reflect.InvocationTargetException;
import java.util.HashMap;
import java.util.Map;

public class BindingTest extends BindingBaseTest implements Serializable {

    public BindingTest() {
    }

    @Test
    public void init_ESCAPE_SEQUENCE_true() throws NoSuchMethodException, InstantiationException, IllegalAccessException, IllegalArgumentException, InvocationTargetException, SecurityException {
        Map<String, Object> params = new HashMap() {
            {
                put("tenantParams", new HashMap<String, String>() {
                    {
                        put("ESCAPE_SEQUENCE", "true");
                    }
                });
                put("cloudParams", new HashMap<String, String>() {
                    {
                        put("yaml", "'a: a'");
                    }
                });
            }
        };

        Binding binding = setupBinding(params);
        assertEquals("true", binding.getProcessorType());
        assertTrue(binding.get("tenant").get("cloud").get("yaml").getValue() instanceof Map);
    }

    @Test
    public void init_ESCAPE_SEQUENCE_default() throws NoSuchMethodException, InstantiationException, IllegalAccessException, IllegalArgumentException, InvocationTargetException, SecurityException {
        Map<String, Object> params = new HashMap();

        Binding binding = setupBinding(params);

        assertEquals("false", binding.getProcessorType());
    }


    @Test
    public void init_UsernamePassword() throws NoSuchMethodException, InstantiationException, IllegalAccessException, IllegalArgumentException, InvocationTargetException, SecurityException {
        Map<String, Object> params = new HashMap() {
            {
                put("tenantParams", new HashMap<String, String>() {
                    {
                        put("#creds{USERNAME,PASSWORD}", "credId");
                    }
                });
            }
        };

        Binding binding = setupBinding(params);
        assertEquals("username", binding.get("tenant").get("USERNAME").getValue());
        assertEquals("pa$$word", binding.get("tenant").get("PASSWORD").getValue());
    }

    @Test
    public void init_NSUsernamePassword() throws NoSuchMethodException, InstantiationException, IllegalAccessException, IllegalArgumentException, InvocationTargetException, SecurityException {
        Map<String, Object> params = new HashMap() {
            {
                put("tenantParams", new HashMap<String, String>() {
                    {
                        put("#credsns{USERNAME,PASSWORD}", "credId");
                    }
                });
            }
        };

        Binding binding = setupBinding(params);
        assertEquals("username", binding.get("tenant").get("USERNAME").getValue());
        assertEquals("pa$$word", binding.get("tenant").get("PASSWORD").getValue());
    }

    @Test
    public void init_CLUsernamePassword() throws NoSuchMethodException, InstantiationException, IllegalAccessException, IllegalArgumentException, InvocationTargetException, SecurityException {
        Map<String, Object> params = new HashMap() {
            {
                put("tenantParams", new HashMap<String, String>() {
                    {
                        put("#credscl{USERNAME,PASSWORD}", "credId");
                    }
                });
            }
        };

        Binding binding = setupBinding(params);
        assertEquals("username", binding.get("tenant").get("USERNAME").getValue());
        assertEquals("pa$$word", binding.get("tenant").get("PASSWORD").getValue());
    }

    @Test
    public void EscapeSequenceProcessingTest() throws IllegalArgumentException, SecurityException {
        Map<String, Object> params = new HashMap() {
            {
                put("tenantParams", new HashMap<String, String>() {
                    {
                        put("param", "first second third");
                        put("param2", "${param.split(' ')[1]}");
                    }
                });
            }
        };

        Binding binding = setupBinding(params);

        Map<String, Object> map = ParametersProcessor.convertParameterMapToObject(new ExpressionLanguage(binding).processDeployment());
        assertEquals("second", map.get("param2"));
    }

    @Test
    public void expressionLanguageExceptionTest() throws IllegalArgumentException, SecurityException {
        Map<String, Object> params = new HashMap() {
            {
                put("tenantParams", new HashMap<String, String>() {
                    {
                        put("param", "first second third");
                        put("param2", "$param.split(\" \")[1]");
                    }
                });
            }
        };

        Binding binding = setupBinding(params);
        ExpressionLanguageException exception = assertThrows(ExpressionLanguageException.class,
                () -> new ExpressionLanguage(binding).processDeployment());
        assertTrue(exception.getMessage().contains("Could not process expression for parameter param2"));
    }

    @Test
    public void groovyFallbackTest() throws IllegalArgumentException, SecurityException {
        Map<String, Object> params = new HashMap() {
            {
                put("tenantParams", new HashMap<String, String>() {
                    {
                        put("param", "first second third");
                        put("param2", "${param instanceof String}");
                    }
                });
            }
        };

        Binding binding = setupBinding(params);
        new ExpressionLanguage(binding).processDeployment();
    }
}
