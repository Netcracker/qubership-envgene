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

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.qubership.cloud.BindingBaseTest;
import org.qubership.cloud.devops.commons.utils.constant.ParametersConstants;
import org.qubership.cloud.devops.commons.pojo.parameterset.ParameterSet;
import org.qubership.cloud.devops.commons.pojo.tenants.model.Tenant;
import org.qubership.cloud.devops.commons.pojo.parameterset.ParameterSetApplication;
import org.qubership.cloud.devops.commons.utils.Parameter;
import org.qubership.cloud.parameters.processor.expression.ExpressionLanguage;
import org.qubership.cloud.parameters.processor.expression.PlainLanguage;
import org.qubership.cloud.parameters.processor.expression.binding.Binding;

import org.junit.jupiter.api.Test;

import java.util.Collections;
import java.util.HashMap;
import java.util.LinkedList;
import java.util.Map;

public class LanguageTest extends BindingBaseTest {
    private Binding prepareBinding() {
        return setupBinding(new HashMap() {
            {
                put("tenantParams", new HashMap<String, String>() {{
                    put("TENANT_PARAM", "tenant");
                    put("TENANT_PARAM_OVERRIDE_BY_APP", "tenant");
                    put("TENANT_PARAM_OVERRIDE_BY_CLOUD", "tenant");
                    put("TENANT_PARAM_OVERRIDE_BY_CLOUD_APP", "tenant");
                    put("TENANT_PARAM_OVERRIDE_BY_NS", "tenant");
                    put("TENANT_PARAM_OVERRIDE_BY_NS_APP", "tenant");
                }});
                put("appParams", new HashMap<String, String>() {{
                    put("APP_PARAM", "app");
                    put("APP_PARAM_OVERRIDE_BY_CLOUD", "app");
                    put("APP_PARAM_OVERRIDE_BY_CLOUD_APP", "app");
                    put("APP_PARAM_OVERRIDE_BY_NS", "app");
                    put("APP_PARAM_OVERRIDE_BY_NS_APP", "app");
                    put("TENANT_PARAM_OVERRIDE_BY_APP", "app");

                }});
                put("cloudParams", new HashMap<String, String>() {{
                    put("CLOUD_PARAM", "cloud");
                    put("CLOUD_PARAM_OVERRIDE_BY_CLOUD_APP", "cloud");
                    put("CLOUD_PARAM_OVERRIDE_BY_NS", "cloud");
                    put("CLOUD_PARAM_OVERRIDE_BY_NS_APP", "cloud");

                    put("TENANT_PARAM_OVERRIDE_BY_CLOUD", "cloud");
                    put("APP_PARAM_OVERRIDE_BY_CLOUD", "cloud");
                }});
                put("cloudAppParams", new HashMap<String, String>() {{
                    put("CLOUD_APP_PARAM", "cloudApp");
                    put("CLOUD_APP_PARAM_OVERRIDE_BY_NS", "cloudApp");
                    put("CLOUD_APP_PARAM_OVERRIDE_BY_NS_APP", "cloudApp");

                    put("TENANT_PARAM_OVERRIDE_BY_CLOUD_APP", "cloudApp");
                    put("APP_PARAM_OVERRIDE_BY_CLOUD_APP", "cloudApp");
                    put("CLOUD_PARAM_OVERRIDE_BY_CLOUD_APP", "cloudApp");
                }});
                put("nsParams", new HashMap<String, String>() {{
                    put("NS_PARAM", "ns");
                    put("NS_PARAM_OVERRIDE_BY_NS_APP", "ns");

                    put("TENANT_PARAM_OVERRIDE_BY_NS", "ns");
                    put("APP_PARAM_OVERRIDE_BY_NS", "ns");
                    put("CLOUD_PARAM_OVERRIDE_BY_NS", "ns");
                    put("CLOUD_APP_PARAM_OVERRIDE_BY_NS", "ns");
                }});
                put("nsAppParams", new HashMap<String, String>() {{
                    put("NS_APP_PARAM", "nsApp");

                    put("TENANT_PARAM_OVERRIDE_BY_NS_APP", "nsApp");
                    put("APP_PARAM_OVERRIDE_BY_NS_APP", "nsApp");
                    put("CLOUD_PARAM_OVERRIDE_BY_NS_APP", "nsApp");
                    put("CLOUD_APP_PARAM_OVERRIDE_BY_NS_APP", "nsApp");
                    put("NS_PARAM_OVERRIDE_BY_NS_APP", "nsApp");
                }});
                put("defaultEscapeSequence", "true");
            }
        });
    }

    @Test
    public void processDeployment_Plain_validate_order() {
        Binding binding = prepareBinding();
        assertMap(new PlainLanguage(binding).processDeployment());
    }

    @Test
    public void processDeployment_Expression_validate_order() {
        Binding binding = prepareBinding();
        assertMap(new ExpressionLanguage(binding).processDeployment());
    }

    public void assertMap(Map<String, Parameter> map) {

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

        HashMap<String, Parameter> checkMap = new HashMap<String, Parameter>() {{
            put("TENANT_PARAM", new Parameter("tenant"));
            put("TENANT_PARAM_OVERRIDE_BY_APP", new Parameter("app"));
            put("TENANT_PARAM_OVERRIDE_BY_CLOUD", new Parameter("cloud"));
            put("TENANT_PARAM_OVERRIDE_BY_CLOUD_APP", new Parameter("cloudApp"));
            put("TENANT_PARAM_OVERRIDE_BY_NS", new Parameter("ns"));
            put("TENANT_PARAM_OVERRIDE_BY_NS_APP", new Parameter("nsApp"));

            put("APP_PARAM", new Parameter("app"));
            put("APP_PARAM_OVERRIDE_BY_CLOUD", new Parameter("cloud"));
            put("APP_PARAM_OVERRIDE_BY_CLOUD_APP", new Parameter("cloudApp"));
            put("APP_PARAM_OVERRIDE_BY_NS", new Parameter("ns"));
            put("APP_PARAM_OVERRIDE_BY_NS_APP", new Parameter("nsApp"));

            put("CLOUD_PARAM", new Parameter("cloud"));
            put("CLOUD_PARAM_OVERRIDE_BY_CLOUD_APP", new Parameter("cloudApp"));
            put("CLOUD_PARAM_OVERRIDE_BY_NS", new Parameter("ns"));
            put("CLOUD_PARAM_OVERRIDE_BY_NS_APP", new Parameter("nsApp"));

            put("CLOUD_APP_PARAM", new Parameter("cloudApp"));
            put("CLOUD_APP_PARAM_OVERRIDE_BY_NS", new Parameter("ns"));
            put("CLOUD_APP_PARAM_OVERRIDE_BY_NS_APP", new Parameter("nsApp"));

            put("NS_PARAM", new Parameter("ns"));
            put("NS_PARAM_OVERRIDE_BY_NS_APP", new Parameter("nsApp"));

            put("NS_APP_PARAM", new Parameter("nsApp"));

        }};

        assertEquals(checkMap, map);

        String tenantOrigin = String.format(ParametersConstants.TENANT_ORIGIN, "tenant");
        assertEquals(tenantOrigin, map.get("TENANT_PARAM").getOrigin());

        String appOrigin = String.format(ParametersConstants.APP_ORIGIN, "application");
        assertEquals(appOrigin, map.get("APP_PARAM").getOrigin());
        assertEquals(appOrigin, map.get("TENANT_PARAM_OVERRIDE_BY_APP").getOrigin());

        String cloudOrigin = String.format(ParametersConstants.CLOUD_ORIGIN, "tenant", "cloud");
        assertEquals(cloudOrigin, map.get("CLOUD_PARAM").getOrigin());
        assertEquals(cloudOrigin, map.get("APP_PARAM_OVERRIDE_BY_CLOUD").getOrigin());
        assertEquals(cloudOrigin, map.get("TENANT_PARAM_OVERRIDE_BY_CLOUD").getOrigin());

        String cloudAppOrigin = String.format(ParametersConstants.CLOUD_APP_ORIGIN, "tenant", "cloud", "application");
        assertEquals(cloudAppOrigin, map.get("CLOUD_APP_PARAM").getOrigin());
        assertEquals(cloudAppOrigin, map.get("TENANT_PARAM_OVERRIDE_BY_CLOUD_APP").getOrigin());
        assertEquals(cloudAppOrigin, map.get("APP_PARAM_OVERRIDE_BY_CLOUD_APP").getOrigin());
        assertEquals(cloudAppOrigin, map.get("CLOUD_PARAM_OVERRIDE_BY_CLOUD_APP").getOrigin());

        String nsOrigin = String.format(ParametersConstants.NS_ORIGIN, "tenant", "cloud", "namespace");
        assertEquals(nsOrigin, map.get("NS_PARAM").getOrigin());
        assertEquals(nsOrigin, map.get("CLOUD_APP_PARAM_OVERRIDE_BY_NS").getOrigin());
        assertEquals(nsOrigin, map.get("CLOUD_PARAM_OVERRIDE_BY_NS").getOrigin());
        assertEquals(nsOrigin, map.get("APP_PARAM_OVERRIDE_BY_NS").getOrigin());
        assertEquals(nsOrigin, map.get("TENANT_PARAM_OVERRIDE_BY_NS").getOrigin());

        String nsAppOrigin = String.format(ParametersConstants.NS_APP_ORIGIN, "tenant", "cloud", "namespace", "application");
        assertEquals(nsAppOrigin, map.get("NS_APP_PARAM").getOrigin());
        assertEquals(nsAppOrigin, map.get("NS_PARAM_OVERRIDE_BY_NS_APP").getOrigin());
        assertEquals(nsAppOrigin, map.get("CLOUD_APP_PARAM_OVERRIDE_BY_NS_APP").getOrigin());
        assertEquals(nsAppOrigin, map.get("CLOUD_PARAM_OVERRIDE_BY_NS_APP").getOrigin());
        assertEquals(nsAppOrigin, map.get("APP_PARAM_OVERRIDE_BY_NS_APP").getOrigin());
        assertEquals(nsAppOrigin, map.get("TENANT_PARAM_OVERRIDE_BY_NS_APP").getOrigin());
    }
}
