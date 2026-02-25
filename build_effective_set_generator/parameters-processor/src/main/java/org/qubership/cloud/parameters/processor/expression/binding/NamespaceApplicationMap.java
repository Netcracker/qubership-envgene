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

import lombok.extern.slf4j.Slf4j;
import org.apache.commons.collections4.MapUtils;
import org.apache.commons.lang.StringUtils;
import org.qubership.cloud.devops.commons.Injector;
import org.qubership.cloud.devops.commons.pojo.applications.model.ApplicationParams;
import org.qubership.cloud.devops.commons.pojo.bom.ApplicationBomDTO;
import org.qubership.cloud.devops.commons.pojo.namespaces.model.Namespace;
import org.qubership.cloud.devops.commons.pojo.profile.model.Profile;
import org.qubership.cloud.devops.commons.utils.BomReaderUtils;
import org.qubership.cloud.devops.commons.utils.Parameter;
import org.qubership.cloud.devops.commons.utils.constant.ParametersConstants;


import java.util.*;

import static org.qubership.cloud.devops.commons.utils.constant.ApplicationConstants.*;


@Slf4j
public class NamespaceApplicationMap extends DynamicMap {

    private final Namespace namespace;

    public NamespaceApplicationMap(Namespace namespace, String defaultApp, Binding binding) {
        super(defaultApp, binding);
        this.namespace = namespace;
    }

    @Override
    public Map<String, Parameter> getMap(String appName) {
        ApplicationParams applicationParams = namespace
                .getApplications()
                .stream()
                .filter(app -> app.getAppName().equals(appName))
                .findAny()
                .orElse(null);

        Map<String, Object> appParams = applicationParams != null ? applicationParams.getAppParams() : new HashMap<>();
        Map<String, Object> configServerParams = applicationParams != null ? applicationParams.getConfigServerParams() : new HashMap<>();
        EscapeMap map = new EscapeMap(appParams, binding,
                String.format(ParametersConstants.NS_APP_ORIGIN, namespace.getCloud().getTenant().getName(), namespace.getCloud().getName(),
                        namespace.getName(), appName));
        EscapeMap configServerMap = new EscapeMap(configServerParams, binding,
                String.format(ParametersConstants.NS_APP_CONFIG_SERVER_ORIGIN, namespace.getCloud().getTenant().getName(), namespace.getCloud().getName(),
                        namespace.getName(), appName));


        map.put("APPLICATION_NAME", appName);

        map.put("config-server", configServerMap);
        try {
            if (binding.getDeployerInputs() != null && binding.getDeployerInputs().getAppVersion() != null) {
                populateAdditionalParams(appName, binding.getDeployerInputs().getAppFileRef(), map);
            }
        } catch (Exception e) {
            throw new RuntimeException(String.format("Failed to get Service data for %s because of %s", appName, e.getMessage()));
        }
        maps.put(appName, map);
        return map;
    }

    private void populateAdditionalParams(String appName, String appFileRef, EscapeMap map) {
        ApplicationBomDTO applicationBomDto = getApplicationBomDto(appName, appFileRef);
        if (applicationBomDto != null) {
            map.put("ARTIFACT_DESCRIPTOR_ARTIFACT_ID", applicationBomDto.getArtifactId());
            map.put("ARTIFACT_DESCRIPTOR_GROUP_ID", applicationBomDto.getGroupId());
            map.put("ARTIFACT_DESCRIPTOR_VERSION", applicationBomDto.getVersion());
            map.put("ARTIFACT_DESCRIPTOR_MAVEN_REPO", applicationBomDto.getMavenRepo());
            map.put("DEPLOYMENT_SESSION_ID", applicationBomDto.getDeployerSessionId());
            map.put(APPR_CHART_NAME, applicationBomDto.getAppChartName());
            map.put(SERVICES, applicationBomDto.getServices());
            map.put(CONFIGURATIONS, applicationBomDto.getConfigurations());
            map.put(FRONTENDS, applicationBomDto.getFrontends());
            map.put(SMARTPLUG, applicationBomDto.getSmartplugs());
            map.put(CDN, applicationBomDto.getCdn());
            map.put(SAMPLREPO, applicationBomDto.getSampleRepo());
            map.put(DEPLOY_DESC, applicationBomDto.getDeployDescriptors());
            map.put(COMMON_DEPLOY_DESC, applicationBomDto.getCommonDeployDescriptors());
            map.put(PER_SERVICE_DEPLOY_PARAMS, applicationBomDto.getPerServiceParams());
            if (MapUtils.isNotEmpty(applicationBomDto.getDeployParams())) {
                applicationBomDto.getDeployParams().forEach((key, value) -> {
                    map.put(key, value);
                });
            }
        }
    }

    private ApplicationBomDTO getApplicationBomDto(String appName, String appFileRef) {
        String baselineProfile = namespace.getBaseline();
        Profile overrideProfile = namespace.getProfile();
        if (StringUtils.isEmpty(baselineProfile)) {
            baselineProfile = namespace.getCloud().getBaseline();
            overrideProfile = namespace.getCloud().getProfile();
        }
        BomReaderUtils bomReaderUtils = Injector.getInstance().get(BomReaderUtils.class);
        String baseline = null;
        if (overrideProfile != null) {
            baseline = overrideProfile.getBaseline();
        } else if (StringUtils.isNotEmpty(baselineProfile)) {
            baseline = baselineProfile;
        }
        return bomReaderUtils.getAppServicesWithProfiles(appName, appFileRef, baseline, overrideProfile);
    }
}
