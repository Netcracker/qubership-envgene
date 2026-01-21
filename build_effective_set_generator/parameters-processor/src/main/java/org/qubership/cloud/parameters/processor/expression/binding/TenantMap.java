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

package org.qubership.cloud.parameters.processor.expression.binding;

import org.qubership.cloud.devops.commons.utils.constant.ParametersConstants;
import org.qubership.cloud.devops.commons.Injector;
import org.qubership.cloud.devops.commons.pojo.tenants.model.Tenant;
import org.qubership.cloud.devops.commons.utils.Parameter;

import java.util.Map;

public class TenantMap extends DynamicMap {
    private String defaultCloud;
    private String defaultNamespace;
    private String defaultApp;
    private boolean mergeE2E;
    private String originalNamespace;

    public TenantMap(String defaultTenant, String defaultCloud, String defaultNamespace, String defaultApp,
                     Binding binding, String originalNamespace) {
        super(defaultTenant, binding);
        this.defaultCloud = defaultCloud;
        this.defaultNamespace = defaultNamespace;
        this.defaultApp = defaultApp;
        this.originalNamespace = originalNamespace;
    }

    public boolean isMergeE2E() {
        return mergeE2E;
    }

    @Override
    public DynamicMap init() {
        DynamicMap result = super.init();
        defaultCloud = null;
        defaultNamespace = null;
        defaultApp = null;
        return result;
    }

    @Override
    public Map<String, Parameter> getMap(String tenantName) {
        Tenant config = Injector.getInstance().getTenantConfigurationService().getTenantByName(tenantName);
        if (config != null) {
            mergeE2E = config.getGlobalParameters().getE2eParameters().isMergeTenantAndE2EParams();
            EscapeMap map = new EscapeMap(config
                    .getGlobalParameters()
                    .getDeployParameters(), binding,
                    String.format(ParametersConstants.TENANT_ORIGIN, tenantName));
            EscapeMap e2e = new EscapeMap(config.getGlobalParameters().getE2eParameters().getEnvParameters(), binding, String.format(ParametersConstants.TENANT_E2E_ORIGIN, tenantName));
            EscapeMap configServer = new EscapeMap(config.getGlobalParameters().getTechnicalConfiguration(), binding, String.format(ParametersConstants.TENANT_CONFIG_SERVER_ORIGIN, tenantName));

            map.put("cloud", new Parameter(new CloudMap(tenantName, defaultCloud, defaultNamespace, defaultApp, binding, originalNamespace).init()));
            map.put("e2e", new Parameter(e2e));
            map.put("TENANTNAME", tenantName);
            map.put("config-server", configServer);
            maps.put(tenantName, map);
            return map;
        }
        return null;
    }
}
