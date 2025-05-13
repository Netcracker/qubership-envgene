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

package org.qubership.cloud.devops.cli.beans;

import org.qubership.cloud.devops.cli.utils.di.CliDI;
import org.qubership.cloud.devops.commons.Injector;
import io.quarkus.runtime.Startup;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.enterprise.inject.Produces;
import lombok.extern.slf4j.Slf4j;
import org.qubership.cloud.devops.commons.service.interfaces.*;
import org.qubership.cloud.devops.commons.utils.BomReaderUtils;
import org.qubership.cloud.devops.commons.utils.CredentialUtils;

@Slf4j
@ApplicationScoped
public class InjectorProvider {

    @Produces
    @ApplicationScoped
    @Startup
    public Injector getInjector(
            NamespaceConfigurationService namespaceConfigurationService,
            TenantConfigurationService tenantConfigurationService,
            CloudConfigurationService cloudConfigurationService,
            ParameterSetService parameterSetService,
            RegistryConfigurationService registryConfigurationService,
            CredentialUtils credentialUtils,
            BomReaderUtils bomReaderUtils
    ) {
        CliDI cliDI = new CliDI();
        Injector di = new Injector(cliDI);
        di.setNamespaceConfigurationService(namespaceConfigurationService);
        di.setTenantConfigurationService(tenantConfigurationService);
        di.setCloudConfigurationService(cloudConfigurationService);
        di.setParameterSetService(parameterSetService);
        di.setRegistryConfigurationService(registryConfigurationService);
        di.setCredentialUtils(credentialUtils);
        di.setBomReaderUtils(bomReaderUtils);
        return di;
    }
}
