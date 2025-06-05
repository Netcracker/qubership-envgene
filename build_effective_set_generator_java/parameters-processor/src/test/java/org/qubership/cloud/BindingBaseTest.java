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

package org.qubership.cloud;

import static org.mockito.ArgumentMatchers.any;

import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

import org.qubership.cloud.devops.commons.Injector;
import org.qubership.cloud.devops.commons.pojo.applications.model.Application;
import org.qubership.cloud.devops.commons.pojo.applications.model.ApplicationParams;
import org.qubership.cloud.devops.commons.pojo.clouds.model.Cloud;
import org.qubership.cloud.devops.commons.pojo.credentials.model.UsernamePasswordCredentials;
import org.qubership.cloud.devops.commons.pojo.namespaces.model.Namespace;
import org.qubership.cloud.devops.commons.pojo.parameterset.ParameterSet;
import org.qubership.cloud.devops.commons.pojo.tenants.model.Tenant;
import org.qubership.cloud.devops.commons.pojo.tenants.model.GlobalE2EParameters;
import org.qubership.cloud.devops.commons.pojo.tenants.model.TenantGlobalParameters;
import org.qubership.cloud.devops.commons.service.interfaces.ApplicationService;
import org.qubership.cloud.devops.commons.service.interfaces.CloudConfigurationService;
import org.qubership.cloud.devops.commons.service.interfaces.NamespaceConfigurationService;
import org.qubership.cloud.devops.commons.service.interfaces.ParameterSetService;
import org.qubership.cloud.devops.commons.service.interfaces.TenantConfigurationService;
import org.qubership.cloud.devops.commons.utils.CredentialUtils;
import org.qubership.cloud.devops.commons.utils.di.MapDI;
import org.qubership.cloud.devops.commons.utils.otel.OpenTelemetryProvider;
import org.qubership.cloud.parameters.processor.expression.binding.Binding;

import io.opentelemetry.api.trace.NoopTracer;
import io.opentelemetry.api.trace.Tracer;

import java.lang.reflect.Constructor;
import java.lang.reflect.InvocationTargetException;
import java.util.Collections;
import java.util.HashMap;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;

public class BindingBaseTest {
    protected Binding setupBinding(Map<String, Object> params) {
        try {
            TenantConfigurationService tenantService = mock(TenantConfigurationService.class);
            Map<String, String> tenantParams = (Map<String, String>) params.get("tenantParams");
            when(tenantService.getTenantByName("tenant")).thenReturn(Tenant.builder().name("tenant").globalParameters(TenantGlobalParameters.builder().deployParameters(tenantParams).e2eParameters(
                    new GlobalE2EParameters(null, null, params.containsKey("tenantParamsE2E") ? (Map<String, String>) params.get("tenantParamsE2E") : new HashMap<>(), false)).build()).build());
            CloudConfigurationService cloudService = mock(CloudConfigurationService.class);
            Cloud cloud = Cloud.builder().build();
            cloud.setTenant(new Tenant("tenant"));
            cloud.setName("cloud");
            if (params.get("cloudParams") != null) {
                cloud.setCloudParams((Map<String, String>) params.get("cloudParams"));
            } else {
                cloud.setCloudParams(Collections.emptyMap());
            }
            cloud.setDbaasCfg(Collections.emptySet());
            if (params.get("cloudAppParams") != null) {
                cloud.setApplicationParams(new LinkedList<>() {{
                    add(new ApplicationParams("application", (Map<String, String>) params.get("cloudAppParams")));
                }});
            } else {
                cloud.setApplicationParams(Collections.emptyList());
            }
            when(cloudService.getCloudByTenant("tenant", "cloud")).thenReturn(cloud);

            NamespaceConfigurationService nsService = mock(NamespaceConfigurationService.class);
            when(nsService.getNamespaceByCloud("cloud", "tenant", "namespace")).thenReturn(
                    Namespace.builder().name("namespace")
                            .labels(null)
                            .cloud(new Cloud(new Tenant("tenant"), "cloud"))
                            .credId("")
                            .applications(new LinkedList<>() {{
                                if (params.get("nsAppParams") != null)
                                    add(new ApplicationParams("application", (Map<String, String>) params.get("nsAppParams")));
                            }})
                            .customParameters((Map<String, String>) params.get("nsParams"))
                            .e2eParameters(null)
                            .mergeCustomPramsAndE2EParams(false)
                            .cleanInstallApprovalRequired(false)
                            .serverSideMerge(false)
                            .configServerParameters(null)
                            .deprecatedDeployParametersNotAllowed(false)
                            .profile(null)
                            .baseline("")
                            .build()
            );

            ApplicationService appService = mock(ApplicationService.class);
            when(appService.getByName("application", "namespace")).thenReturn(
                    Application.builder()
                            .name("application")
                            .params(params.get("appParams") != null ? (Map<String, String>) params.get("appParams") : Collections.emptyMap())
                            .build()
            );

            CredentialUtils credentialUtils = mock(CredentialUtils.class);
            when(credentialUtils.getCredentialsById(any())).thenReturn(new UsernamePasswordCredentials("username", "pa$$word"));

            MapDI mapDI = new MapDI().withBean(credentialUtils);
            mapDI.bind(OpenTelemetryProvider.class, new OpenTelemetryProvider() {
                @Override
                public Tracer getTracer() {
                    return new NoopTracer();
                }

                @Override
                public <T, E extends Exception> T withSpan(String spanName, ThrowingSupplier<T, E> delegate) throws E {
                    return delegate.get();
                }
            });
            new Injector(mapDI);
            Injector provider = new Injector(mapDI);
            provider.setTenantConfigurationService(tenantService);
            provider.setCloudConfigurationService(cloudService);
            provider.setNamespaceConfigurationService(nsService);
            provider.add(appService);
            Constructor<Binding> constructor = Binding.class.getDeclaredConstructor(String.class);
            constructor.setAccessible(true);
            Binding binding = constructor.newInstance(params.get("defaultEscapeSequence") != null ? params.get("defaultEscapeSequence") : "false")
                    .init("tenant", "cloud", "namespace", "application");
            return binding;

        } catch (NoSuchMethodException | InstantiationException | IllegalAccessException | IllegalArgumentException |
                 InvocationTargetException | SecurityException e) {
            throw new RuntimeException(e);
        }
    }
}
