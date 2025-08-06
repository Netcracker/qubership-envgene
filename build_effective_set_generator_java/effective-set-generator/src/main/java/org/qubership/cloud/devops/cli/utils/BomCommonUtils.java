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

package org.qubership.cloud.devops.cli.utils;

import com.fasterxml.jackson.core.type.TypeReference;
import jakarta.enterprise.context.ApplicationScoped;
import org.cyclonedx.model.AttachmentText;
import org.cyclonedx.model.Component;
import org.cyclonedx.model.Property;
import org.cyclonedx.model.component.data.ComponentData;
import org.cyclonedx.model.component.data.Content;
import org.qubership.cloud.devops.commons.exceptions.BomProcessingException;
import org.qubership.cloud.devops.commons.pojo.bom.EntitiesMap;
import org.qubership.cloud.devops.commons.pojo.profile.model.Profile;
import org.qubership.cloud.devops.commons.pojo.registries.dto.RegistrySummaryDTO;
import org.qubership.cloud.devops.commons.repository.interfaces.FileDataConverter;
import org.qubership.cloud.devops.commons.service.interfaces.ProfileService;
import org.qubership.cloud.devops.commons.service.interfaces.RegistryConfigurationService;
import org.qubership.cloud.parameters.processor.dto.DeployOptions;
import org.qubership.cloud.parameters.processor.dto.DeploymentConfig;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Collectors;
import java.util.stream.Stream;

import static org.qubership.cloud.devops.cli.exceptions.constants.ExceptionMessage.REGISTRY_EXTRACT_FAILED;
import static org.qubership.cloud.devops.commons.utils.ConsoleLogger.logError;

@ApplicationScoped
public class BomCommonUtils {
    private final FileDataConverter fileDataConverter;
    private final ProfileService profileService;
    private final RegistryConfigurationService registryConfigurationService;
    private static final List<String> SERVICE_MIME_TYPES = List.of("application/vnd.qubership.configuration.smartplug", "application/vnd.qubership.configuration.frontend", "application/vnd.qubership.configuration.cdn", "application/vnd.qubership.configuration", "application/vnd.qubership.service", "application/octet-stream");
    private static final Pattern DOCKER_PATTERN = Pattern.compile("(pkg:docker.*)\\?registry_id=(.*)&repository_id=(.*)");

    public BomCommonUtils(FileDataConverter fileDataConverter, RegistryConfigurationService registryConfigurationService, ProfileService profileService) {
        this.fileDataConverter = fileDataConverter;
        this.registryConfigurationService = registryConfigurationService;
        this.profileService = profileService;
    }

    public void getServiceEntities(EntitiesMap entitiesMap, List<Component> components) {
        for (Component component : components) {
            if (SERVICE_MIME_TYPES.contains(component.getMimeType())) {
                entitiesMap.getServiceMap().put(component.getName(), new HashMap<>());
            }
        }
    }

    public void getEntities(EntitiesMap entitiesMap, List<Component> components, String appName, String baseline, Profile override) {
        for (Component component : components) {
            if (component.getMimeType().equals("application/vnd.qubership.service")) {
                processServiceComponent(entitiesMap.getServiceMap(), component, appName, baseline, override);
            } else if (component.getMimeType().equals("application/vnd.qubership.configuration.smartplug")) {
                getOtherComponents(entitiesMap.getSmartplugMap(), component, "application/vnd.osgi.bundle");
            } else if (component.getMimeType().equals("application/vnd.qubership.configuration.frontend")) {
                getOtherComponents(entitiesMap.frontEndMap, component, "application/zip");
            } else if (component.getMimeType().equals("application/vnd.qubership.configuration")) {
                getOtherComponents(entitiesMap.getConfigurationMap(), component, "application/zip");
            } else if (component.getMimeType().equals("application/vnd.qubership.configuration.cdn")) {
                getOtherComponents(entitiesMap.getCdnMap(), component, "application/zip");
            } else if (component.getMimeType().equals("application/vnd.qubership.configuration.sampleRepo")) {
                getOtherComponents(entitiesMap.getRepoMap(), component, "application/zip");
            }
        }
    }

    private void getOtherComponents(Map<String, Map<String, Object>> configMap, Component component, String type) {
        Map<String, Object> configParams = new TreeMap<>();
        List<Component>  subComponents = component.getComponents().stream().filter(artifact -> artifact.getMimeType().equals(type)).collect(Collectors.toList());
        if (subComponents.size() > 1) {
            throw new BomProcessingException("Multiple artifacts of type"+ type+" is not allowed");
        }
        Component subComponent = subComponents.get(0);
        if (subComponent != null) {
            configParams.put("artifact.gav", String.format("%s:%s:%s", subComponent.getName(), subComponent.getGroup(), subComponent.getVersion()));
            configParams.put("artifact.groupId", subComponent.getGroup());
            configParams.put("artifact.artifactId", subComponent.getName());
            configParams.put("artifact.version", subComponent.getVersion());
            configMap.put(component.getName(), configParams);
        }
    }

    private void processServiceComponent(Map<String, Map<String, Object>> serviceMap, Component component, String appName, String baseline, Profile override) {
        String gitBranch = getPropertyValue(component, "git_branch");
        String imageType = getPropertyValue(component, "image_type");

        String imageName = null;
        String dockerRepo = null;
        String dockerTag = null;
        boolean isFacadeGateway = false;
        RegistrySummaryDTO registrySummaryDTO = null;
        Map<String, String> profileValues = new HashMap<>();

        for (Component subComponent : component.getComponents()) {
            switch (subComponent.getMimeType()) {
                case "application/vnd.docker.image":
                    imageName = subComponent.getName();
                    dockerRepo = subComponent.getGroup();
                    dockerTag = subComponent.getVersion();
                    registrySummaryDTO = getRegistrySummaryDTO(subComponent, DOCKER_PATTERN);
                    break;
                case "application/vnd.qubership.configuration.declarative-configuration":
                    isFacadeGateway = extractGatewayFlag(subComponent);
                    break;
                case "application/vnd.qubership.resource-profile-baseline":
                    profileValues = extractProfileValues(subComponent, appName, component.getName(), override, baseline);
                    break;

            }
        }

        Map<String, Object> serviceParams = new HashMap<>();
        serviceParams.put("SERVICE_NAME", component.getName());
        serviceParams.put("SERVICE_TYPE", imageType != null ? imageType : "");
        serviceParams.put("TAG", dockerTag != null ? dockerTag : "");
        serviceParams.put("DOCKER_TAG", imageName != null ? imageName : "");
        serviceParams.put("BRANCH", gitBranch);
        serviceParams.put("IMAGE_REPOSITORY", String.format("%s/%s/%s", registryConfigurationService.getDockerRepoForService(registrySummaryDTO), dockerRepo, imageName));
        if (isFacadeGateway) {
            serviceParams.put("OPENSHIFT_SERVICE_NAME", component.getName() + "v1");
            serviceParams.put("DEPLOYMENT_RESOURCE_NAME", component.getName() + "v1");
            serviceParams.put("DEPLOYMENT_VERSION", "v1");
        }
        if (profileValues != null && !profileValues.isEmpty()) {
            serviceParams.putAll(profileValues);
        }
        serviceMap.put(component.getName(), serviceParams);
    }

    public String getPropertyValue(Component component, String propertyName) {
        return safePropertyStream(component)
                .filter(property -> propertyName.equals(property.getName()))
                .map(Property::getValue)
                .findFirst()
                .orElse("");
    }

    public Stream<Property> safePropertyStream(Component component) {
        return component.getProperties() != null
                ? component.getProperties().stream()
                : Stream.empty();
    }

    private boolean extractGatewayFlag(Component dataComponent) {
        try {
            return dataComponent.getData().stream()
                    .map(ComponentData::getContents)
                    .map(Content::getAttachment)
                    .map(AttachmentText::getText)
                    .map(encodedText -> fileDataConverter.decodeAndParse(encodedText, DeploymentConfig.class))
                    .map(deploymentConfig -> {
                        DeployOptions deployOptions = deploymentConfig.getDeployOptions();
                        return deployOptions != null && deployOptions.isGenerateFacadeGateway();
                    })
                    .findFirst()
                    .orElse(false);
        } catch(Exception e) {
            return false;
        }
    }

    protected static RegistrySummaryDTO getRegistrySummaryDTO(Component component, Pattern pattern) {
        Matcher regMatcher = pattern.matcher(component.getPurl());
        RegistrySummaryDTO registrySummaryDTO = null;
        if (regMatcher.find()) {
            String registryName = regMatcher.group(2);
            registryName = registryName.replace("%20", " ");
            String repoId = regMatcher.group(3);
            registrySummaryDTO = RegistrySummaryDTO.builder().name(registryName).repoId(repoId)
                    .build();
        } else {
            logError(String.format(REGISTRY_EXTRACT_FAILED, component.getName()));
        }
        return registrySummaryDTO;
    }

    private Map<String, String> extractProfileValues(Component dataComponent, String appName, String serviceName,
                                                     Profile overrideProfile, String baseline) {
        Map<String, String> profileValues = new HashMap<>();
        if (baseline == null) {
            profileService.setOverrideProfiles(appName, serviceName, overrideProfile, profileValues);
        }
        for (ComponentData data : dataComponent.getData()) {
            if (baseline != null && baseline.equals(data.getName().split("\\.")[0])) {
                Content content = data.getContents();
                String encodedText = content.getAttachment().getText();
                profileValues = fileDataConverter.decodeAndParse(encodedText, new TypeReference<HashMap<String, String>>() {
                });

                profileService.setOverrideProfiles(appName, serviceName, overrideProfile, profileValues);
                break;
            }
        }
        return profileValues;
    }
}
