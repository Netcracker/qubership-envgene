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

package org.qubership.cloud.devops.commons;

import org.qubership.cloud.devops.commons.utils.BomReaderUtils;
import org.qubership.cloud.devops.commons.utils.CredentialUtils;
import org.qubership.cloud.devops.commons.utils.di.DIWrapper;
import org.qubership.cloud.devops.commons.utils.di.MapDI;
import lombok.Getter;
import org.qubership.cloud.devops.commons.service.interfaces.*;

@Getter
public class Injector {

    public volatile DIWrapper di;
    private static Injector instance;

    public Injector() {
        di = new MapDI();
        instance = this;
    }

    public Injector(DIWrapper di) {
        this.di = di;
        instance = this;
    }

    public static Injector getInstance() {
        if (instance == null) {
            return new Injector();
        }
        return instance;
    }

    public CredentialUtils getCredentialUtils() {
        return di.get(CredentialUtils.class);
    }

    public TenantConfigurationService getTenantConfigurationService() {
        return di.get(TenantConfigurationService.class);
    }

    public void setTenantConfigurationService(TenantConfigurationService tenantConfigurationService) {
        di.add(tenantConfigurationService);
    }

    public NamespaceConfigurationService getNamespaceConfigurationService() {
        return di.get(NamespaceConfigurationService.class);
    }

    public BomReaderUtils getBomReaderUtils() {
        return di.get(BomReaderUtils.class);
    }

    public void setNamespaceConfigurationService(NamespaceConfigurationService namespaceConfigurationService) {
        di.add(namespaceConfigurationService);
    }

    public void setCredentialUtils(CredentialUtils credentialUtils) {
        di.add(credentialUtils);
    }

    public void setBomReaderUtils(BomReaderUtils bomReaderUtils) {
        di.add(bomReaderUtils);
    }

    public CloudConfigurationService getCloudConfigurationService() {
        return di.get(CloudConfigurationService.class);
    }

    public void setCloudConfigurationService(CloudConfigurationService cloudConfigurationService) {
        di.add(cloudConfigurationService);
    }

    public ParameterSetService getParameterSetService() {
        return get(ParameterSetService.class);
    }

    public void setParameterSetService(ParameterSetService parameterSetService) {
        di.add(parameterSetService);
    }

    public RegistryConfigurationService getRegistryConfigurationService() {
        return get(RegistryConfigurationService.class);
    }

    public void setRegistryConfigurationService(RegistryConfigurationService registryConfigurationService) {
        di.add(registryConfigurationService);
    }

    public void setInputDataService(InputDataService inputDataService) {
        di.add(inputDataService);
    }

    public InputDataService getInputDataService() {
        return di.get(InputDataService.class);
    }

    public <T> T get(Class<T> clazz) {
        return di.get(clazz);
    }

    public <T> void add(T object) {
        di.add(object);
    }

}
