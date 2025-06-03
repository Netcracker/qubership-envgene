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
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.collections4.CollectionUtils;
import org.apache.commons.lang3.StringUtils;
import org.cyclonedx.model.Bom;
import org.cyclonedx.model.Component;
import org.cyclonedx.model.Property;
import org.cyclonedx.model.component.data.ComponentData;
import org.cyclonedx.model.component.data.Content;
import org.qubership.cloud.devops.cli.pojo.dto.shared.SharedData;
import org.qubership.cloud.devops.commons.exceptions.BomProcessingException;
import org.qubership.cloud.devops.commons.pojo.bom.ApplicationBomDTO;
import org.qubership.cloud.devops.commons.pojo.bom.EntitiesMap;
import org.qubership.cloud.devops.commons.pojo.profile.model.Profile;
import org.qubership.cloud.devops.commons.pojo.registries.dto.RegistrySummaryDTO;
import org.qubership.cloud.devops.commons.repository.interfaces.FileDataConverter;
import org.qubership.cloud.devops.commons.service.interfaces.ProfileService;
import org.qubership.cloud.devops.commons.service.interfaces.RegistryConfigurationService;
import org.qubership.cloud.devops.commons.utils.ServiceArtifactType;

import java.io.File;
import java.util.*;
import java.util.regex.Pattern;

@ApplicationScoped
@Slf4j
public class BomReaderUtilsImplV2 {
    private static final Pattern MAVEN_PATTERN = Pattern.compile("(pkg:maven.*)\\?registry_id=(.*)&repository_id=(.*)");
    private static final List<String> IMAGE_SERVICE_MIME_TYPES = List.of("application/vnd.qubership.service", "application/octet-stream");
    private static final List<String> CONFIG_SERVICE_MIME_TYPES = List.of("application/vnd.qubership.configuration.smartplug", "application/vnd.qubership.configuration.frontend", "application/vnd.qubership.configuration.cdn", "application/vnd.qubership.configuration");
    private static final List<String> SUB_SERVICE_ARTIFACT_MIME_TYPES = List.of("application/xml", "application/zip", "application/vnd.osgi.bundle", "application/java-archive");
    private final FileDataConverter fileDataConverter;
    private final ProfileService profileService;
    private final RegistryConfigurationService registryConfigurationService;
    private final SharedData sharedData;
    private final BomCommonUtils bomCommonUtils;

    public BomReaderUtilsImplV2(FileDataConverter fileDataConverter, ProfileService profileService, RegistryConfigurationService registryConfigurationService, SharedData sharedData, BomCommonUtils bomCommonUtils) {
        this.fileDataConverter = fileDataConverter;
        this.profileService = profileService;
        this.registryConfigurationService = registryConfigurationService;
        this.sharedData = sharedData;
        this.bomCommonUtils = bomCommonUtils;
    }

    public ApplicationBomDTO getAppServicesWithProfiles(String appName, String appFileRef, String baseline, Profile override) {
        Bom bomContent = fileDataConverter.parseSbomFile(new File(appFileRef));
        EntitiesMap entitiesMap = new EntitiesMap();
        try {
            Component component = bomContent.getMetadata().getComponent();
            if (component.getMimeType().contains("application")) {
                ApplicationBomDTO applicationBomDto = component.getComponents()
                        .stream()
                        .map(subComp -> {
                            RegistrySummaryDTO registrySummaryDTO = bomCommonUtils.getRegistrySummaryDTO(subComp, MAVEN_PATTERN);
                            String mavenRepoName = registryConfigurationService.getMavenRepoForApp(registrySummaryDTO);
                            return ApplicationBomDTO.builder().name(appName).artifactId(subComp.getName()).groupId(subComp.getGroup())
                                    .version(subComp.getVersion()).mavenRepo(mavenRepoName).build();
                        }).findFirst().orElse(null);

                bomCommonUtils.getServiceEntities(entitiesMap, bomContent.getComponents());

                getPerServiceEntities(entitiesMap, bomContent.getComponents(), appName, baseline, override, bomContent);

                populateEntityDeployDescParams(entitiesMap, bomContent.getComponents(), bomContent);

                if (applicationBomDto != null) {
                    applicationBomDto.setServices(entitiesMap.getServiceMap());
                    applicationBomDto.setPerServiceParams(entitiesMap.getPerServiceParams());
                    applicationBomDto.setDeployDescriptors(entitiesMap.getDeployDescParamsMap());
                    applicationBomDto.setCommonDeployDescriptors(entitiesMap.getCommonParamsMap());
                }
                return applicationBomDto;
            }
        } catch (Exception e) {
            throw new BomProcessingException("Error reading application sbom due to " + e.getMessage());
        }
        return null;
    }

    private void populateEntityDeployDescParams(EntitiesMap entitiesMap, List<Component> components, Bom bomContent) {
        Map<String, Object> commonParamsMap = new TreeMap<>();
        commonParamsMap.put("APPLICATION_NAME", bomContent.getMetadata().getComponent().getName());
        if (StringUtils.isNotEmpty(sharedData.getExtraParams())) {
            commonParamsMap.put("DEPLOYMENT_SESSION_ID", sharedData.getExtraParams());
        } else {
            commonParamsMap.put("DEPLOYMENT_SESSION_ID", UUID.randomUUID().toString());
        }
        for (Component component : components) {
            if (IMAGE_SERVICE_MIME_TYPES.contains(component.getMimeType())) {
                entitiesMap.getCommonParamsMap().put(component.getName(), commonParamsMap);
                processImageServiceComponentDeployDescParams(entitiesMap.getDeployDescParamsMap(), component);
            } else if (CONFIG_SERVICE_MIME_TYPES.contains(component.getMimeType())) {
                entitiesMap.getCommonParamsMap().put(component.getName(), commonParamsMap);
                processConfigServiceComponentDeployDescParams(entitiesMap.getDeployDescParamsMap(), component);
            }
        }
    }

    private void processConfigServiceComponentDeployDescParams(Map<String, Map<String, Object>> deployParamsMap, Component component) {
        Map<String, Object> deployDescParams = new TreeMap<>();
        ServiceArtifactType serviceArtifactType = ServiceArtifactType.of(component.getMimeType());

        Map<String, Object> primaryArtifactMap = new TreeMap<>();
        List<Map<String, Object>> artifacts = new ArrayList<>();
        for (Component subComponent : component.getComponents()) {
            if (subComponent.getMimeType().equalsIgnoreCase(serviceArtifactType.getArtifactMimeType())) {
                primaryArtifactMap.put("artifact.artifactId", subComponent.getName());
                primaryArtifactMap.put("artifact.groupId", subComponent.getGroup());
                primaryArtifactMap.put("artifact.version", subComponent.getVersion());
            } else if (SUB_SERVICE_ARTIFACT_MIME_TYPES.contains(subComponent.getMimeType())) {
                Map<String, Object> artifactMap = new TreeMap<>();
                artifactMap.put("artifact_id", "");
                artifactMap.put("artifact_path", "");
                artifactMap.put("artifact_type", "");
                artifactMap.put("classifier", getPropertyValue(subComponent, "classifier"));
                artifactMap.put("deploy_params", "");
                artifactMap.put("gav", "");
                artifactMap.put("group_id", "");
                artifactMap.put("id", subComponent.getGroup() + ":" + subComponent.getName() + ":" + subComponent.getVersion());
                artifactMap.put("name", subComponent.getName() + "-" + subComponent.getVersion() + "-" + getPropertyValue(subComponent, "type"));
                artifactMap.put("repository", "");
                artifactMap.put("type", getPropertyValue(component, "type"));
                artifactMap.put("url", "");
                artifactMap.put("version", "");
                artifacts.add(artifactMap);
            }
        }
        deployDescParams.put("artifact", primaryArtifactMap);
        deployDescParams.put("artifacts", artifacts);
        deployDescParams.put("build_id_dtrust", getPropertyValue(component, "build_id_dtrust"));
        deployDescParams.put("git_branch", getPropertyValue(component, "git_branch"));
        deployDescParams.put("git_revision", getPropertyValue(component, "git_revision"));
        deployDescParams.put("git_url", getPropertyValue(component, "git_url"));
        deployDescParams.put("maven_repository", getPropertyValue(component, "maven_repository"));
        deployDescParams.put("name", component.getName());
        deployDescParams.put("service_name", component.getName());
        deployDescParams.put("tArtifactNames", new TreeMap<String, String>());
        deployDescParams.put("type", getPropertyValue(component, "type"));
        deployDescParams.put("version", component.getVersion());


        deployParamsMap.put(component.getName(), deployDescParams);
    }

    private void processImageServiceComponentDeployDescParams(Map<String, Map<String, Object>> deployParamsMap, Component component) {
        Map<String, Object> deployDescParams = new TreeMap<>();

        for (Component subComponent : component.getComponents()) {
            if (subComponent.getMimeType().equalsIgnoreCase("application/vnd.docker.image")) {
                deployDescParams.put("docker_digest", CollectionUtils.isNotEmpty(subComponent.getHashes()) ? subComponent.getHashes().get(0).getValue() : "");
                deployDescParams.put("docker_repository_name", subComponent.getGroup());
                deployDescParams.put("docker_tag", subComponent.getVersion());
                deployDescParams.put("image_name", subComponent.getName());
            }
        }
        deployDescParams.put("deploy_param", getPropertyValue(component, "deploy_param"));
        deployDescParams.put("artifacts", new ArrayList<>());
        deployDescParams.put("docker_registry", getPropertyValue(component, "docker_registry"));
        deployDescParams.put("full_image_name", getPropertyValue(component, "full_image_name"));
        deployDescParams.put("git_branch", getPropertyValue(component, "git_branch"));
        deployDescParams.put("git_revision", getPropertyValue(component, "git_revision"));
        deployDescParams.put("git_url", getPropertyValue(component, "git_url"));
        deployDescParams.put("image", getPropertyValue(component, "full_image_name"));
        deployDescParams.put("image_type", getPropertyValue(component, "image_type"));
        deployDescParams.put("name", component.getName());
        deployDescParams.put("promote_artifacts", getPropertyValue(component, "promote_artifacts"));
        deployDescParams.put("qualifier", getPropertyValue(component, "qualifier"));
        deployDescParams.put("version", component.getVersion());

        deployParamsMap.put(component.getName(), deployDescParams);
    }
    private String getPropertyValue(Component component, String propertyName) {
        return component.getProperties().stream()
                .filter(property -> propertyName.equals(property.getName()))
                .map(Property::getValue)
                .findFirst()
                .orElse(null);
    }

    private void getPerServiceEntities(EntitiesMap entitiesMap, List<Component> components, String appName, String baseline, Profile override, Bom bomContent) {
        for (Component component : components) {
            if (IMAGE_SERVICE_MIME_TYPES.contains(component.getMimeType())) {
                processImageServiceComponent(entitiesMap.getPerServiceParams(), component, appName, baseline, override, bomContent);
            } else if (CONFIG_SERVICE_MIME_TYPES.contains(component.getMimeType())) {
                processConfigServiceComponent(entitiesMap.getPerServiceParams(), component, appName, baseline, override, bomContent);
            }
        }
    }

    private void processConfigServiceComponent(Map<String, Map<String, Object>> serviceMap, Component component, String appName, String baseline, Profile override, Bom bomContent) {
        Map<String, String> profileValues = new TreeMap<>();
        Map<String, Object> serviceParams = new TreeMap<>();

        serviceParams.put("ARTIFACT_DESCRIPTOR_VERSION", bomContent.getMetadata().getComponent().getVersion());
        serviceParams.put("DEPLOYMENT_RESOURCE_NAME", component.getName() + "-v1");
        serviceParams.put("DEPLOYMENT_VERSION", "v1");
        serviceParams.put("SERVICE_NAME", component.getName());


        for (Component subComponent : component.getComponents()) {
            if (subComponent.getMimeType().equalsIgnoreCase("application/vnd.qubership.resource-profile-baseline")) {
                profileValues = extractProfileValues(subComponent, appName, component.getName(), override, baseline);
            }
        }

        if (profileValues != null && !profileValues.isEmpty()) {
            serviceParams.putAll(profileValues);
        }
        serviceMap.put(component.getName(), serviceParams);
    }

    private void processImageServiceComponent(Map<String, Map<String, Object>> serviceMap, Component component, String appName, String baseline, Profile override, Bom bomContent) {
        Map<String, String> profileValues = new TreeMap<>();
        Map<String, Object> serviceParams = new TreeMap<>();
        String tag = "";

        serviceParams.put("ARTIFACT_DESCRIPTOR_VERSION", bomContent.getMetadata().getComponent().getVersion());
        serviceParams.put("DEPLOYMENT_RESOURCE_NAME", component.getName() + "-v1");
        serviceParams.put("DEPLOYMENT_VERSION", "v1");
        serviceParams.put("SERVICE_NAME", component.getName());
        String dockerTag = getPropertyValue(component, "full_image_name");
        serviceParams.put("DOCKER_TAG", dockerTag);
        serviceParams.put("IMAGE_REPOSITORY", StringUtils.isNotEmpty(dockerTag) ? dockerTag.split(":")[0] : "");

        for (Component subComponent : component.getComponents()) {
            if (subComponent.getMimeType().equalsIgnoreCase("application/vnd.docker.image")) {
                tag = subComponent.getVersion();
            } else if (subComponent.getMimeType().equalsIgnoreCase("application/vnd.qubership.resource-profile-baseline")) {
                profileValues = extractProfileValues(subComponent, appName, component.getName(), override, baseline);
            }
        }
        serviceParams.put("TAG", tag);
        if (profileValues != null && !profileValues.isEmpty()) {
            serviceParams.putAll(profileValues);
        }
        serviceMap.put(component.getName(), serviceParams);
    }

    private Map<String, String> extractProfileValues(Component dataComponent, String appName, String serviceName,
                                                     Profile overrideProfile, String baseline) {
        Map<String, String> profileValues = new TreeMap<>();

        for (ComponentData data : dataComponent.getData()) {
            if (baseline.equals(data.getName().split("\\.")[0])) {
                Content content = data.getContents();
                String encodedText = content.getAttachment().getText();
                profileValues = fileDataConverter.decodeAndParse(encodedText, new TypeReference<TreeMap<String, String>>() {
                });

                profileService.setOverrideProfiles(appName, serviceName, overrideProfile, profileValues);
                break;
            }
        }
        return profileValues;
    }
}
