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
import org.apache.commons.collections4.MapUtils;
import org.apache.commons.lang3.StringUtils;
import org.cyclonedx.model.Bom;
import org.cyclonedx.model.Component;
import org.cyclonedx.model.Property;
import org.cyclonedx.model.component.data.ComponentData;
import org.cyclonedx.model.component.data.Content;
import org.qubership.cloud.devops.cli.exceptions.MandatoryParameterException;
import org.qubership.cloud.devops.cli.pojo.dto.shared.SharedData;
import org.qubership.cloud.devops.commons.exceptions.AppChartValidationException;
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

import static org.qubership.cloud.devops.commons.utils.constant.ApplicationConstants.*;

@ApplicationScoped
@Slf4j
public class BomReaderUtilsImplV2 {
    private static final Pattern MAVEN_PATTERN = Pattern.compile("(pkg:maven.*)\\?registry_id=(.*)&repository_id=(.*)");
    private static final List<String> IMAGE_SERVICE_MIME_TYPES = List.of(APPLICATION_VND_QUBERSHIP_SERVICE, APPLICATION_OCTET_STREAM);
    private static final List<String> CONFIG_SERVICE_MIME_TYPES = List.of(APPLICATION_VND_QUBERSHIP_CONFIGURATION_SMARTPLUG, APPLICATION_VND_QUBERSHIP_CONFIGURATION_FRONTEND, APPLICATION_VND_QUBERSHIP_CONFIGURATION_CDN, APPLICATION_VND_QUBERSHIP_CONFIGURATION);
    private static final List<String> SUB_SERVICE_ARTIFACT_MIME_TYPES = List.of(APPLICATION_XML, APPLICATION_ZIP, APPLICATION_VND_OSGI_BUNDLE, APPLICATION_JAVA_ARCHIVE);
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
        if (bomContent == null) {
            return null;
        }
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

                validateAppChart(entitiesMap, bomContent.getComponents());

                getPerServiceEntities(entitiesMap, bomContent.getComponents(), appName, baseline, override, bomContent);

                populateEntityDeployDescParams(entitiesMap, bomContent.getComponents(), bomContent);

                if (applicationBomDto != null) {
                    applicationBomDto.setServices(entitiesMap.getServiceMap());
                    applicationBomDto.setDeployerSessionId(entitiesMap.getDeployerSessionId());
                    applicationBomDto.setPerServiceParams(entitiesMap.getPerServiceParams());
                    applicationBomDto.setDeployDescriptors(entitiesMap.getDeployDescParamsMap());
                    applicationBomDto.setCommonDeployDescriptors(entitiesMap.getCommonParamsMap());
                    applicationBomDto.setAppChartName(entitiesMap.getAppChartName());
                }
                return applicationBomDto;
            }
        } catch (Exception e) {
            throw new BomProcessingException("error reading application sbom \n Root Cause: " + e.getMessage());
        }
        return null;
    }

    private void populateEntityDeployDescParams(EntitiesMap entitiesMap, List<Component> components, Bom bomContent) {
        Map<String, Object> commonParamsMap = new TreeMap<>();
        commonParamsMap.put("APPLICATION_NAME", bomContent.getMetadata().getComponent().getName());
        commonParamsMap.put("MANAGED_BY", "argocd");
        if (StringUtils.isNotEmpty(sharedData.getDeploymentSessionId())) {
            commonParamsMap.put("DEPLOYMENT_SESSION_ID", sharedData.getDeploymentSessionId());
            entitiesMap.setDeployerSessionId(sharedData.getDeploymentSessionId());
        } else {
            String deployerSessionId = UUID.randomUUID().toString();
            commonParamsMap.put("DEPLOYMENT_SESSION_ID", deployerSessionId);
            entitiesMap.setDeployerSessionId(deployerSessionId);
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
        String entity = "service:" + component.getName();
        Map<String, Object> primaryArtifactMap = new TreeMap<>();
        List<Map<String, Object>> artifacts = new ArrayList<>();
        Map<String, Object> tArtifactMap = new TreeMap<>();
        if (CollectionUtils.isNotEmpty(component.getComponents())) {
            for (Component subComponent : component.getComponents()) {
                entity = "sub component '" + subComponent.getName() + "' of service:" + component.getName();
                if (subComponent.getMimeType().equalsIgnoreCase(serviceArtifactType.getArtifactMimeType())) {
                    populateOptionalParam(primaryArtifactMap, "artifactId", subComponent.getName());
                    populateOptionalParam(primaryArtifactMap, "groupId", subComponent.getGroup());
                    populateOptionalParam(primaryArtifactMap, "version", subComponent.getVersion());
                }
                if (SUB_SERVICE_ARTIFACT_MIME_TYPES.contains(subComponent.getMimeType())) {
                    String name = checkIfMandatory(subComponent.getName(), "name", entity);
                    String version = checkIfMandatory(subComponent.getVersion(), "version", entity);
                    Map<String, Object> artifactMap = new TreeMap<>();
                    artifactMap.put("artifact_id", "");
                    artifactMap.put("artifact_path", "");
                    artifactMap.put("artifact_type", "");
                    artifactMap.put("classifier", getPropertyValue(subComponent, "classifier", null, true, entity));
                    artifactMap.put("deploy_params", "");
                    artifactMap.put("gav", "");
                    artifactMap.put("group_id", "");
                    artifactMap.put("id", checkIfMandatory(subComponent.getGroup(), "group", entity) + ":" + name + ":" + version);
                    artifactMap.put("name", name + "-" + version + "." +
                            getPropertyValue(subComponent, "type", null, true, entity));
                    artifactMap.put("repository", "");
                    artifactMap.put("type", getPropertyValue(subComponent, "type", null, true, entity));
                    artifactMap.put("url", "");
                    artifactMap.put("version", "");
                    artifacts.add(artifactMap);
                }
                if (APPLICATION_ZIP.equalsIgnoreCase(subComponent.getMimeType())) {
                    String classifier = getPropertyValue(subComponent, "classifier", null, true, entity);
                    String name = subComponent.getName();
                    String version = subComponent.getVersion();
                    if (StringUtils.isNotBlank(classifier)) {
                        tArtifactMap.put(classifier, name + "-" + version + "-" + classifier + ".zip");
                    } else {
                        tArtifactMap.put("ecl", name + "-" + version + ".zip");
                    }
                }
            }
        }
        deployDescParams.put("tArtifactNames", tArtifactMap);
        deployDescParams.put("artifact", primaryArtifactMap);
        deployDescParams.put("artifacts", artifacts);
        deployDescParams.put("build_id_dtrust", getPropertyValue(component, "build_id_dtrust", null, true, entity));
        deployDescParams.put("git_branch", getPropertyValue(component, "git_branch", null, true, entity));
        deployDescParams.put("git_revision", getPropertyValue(component, "git_revision", null, true, entity));
        deployDescParams.put("git_url", getPropertyValue(component, "git_url", null, true, entity));
        deployDescParams.put("maven_repository", getPropertyValue(component, "maven_repository", null, true, entity));
        deployDescParams.put("name", checkIfMandatory(component.getName(), "name", entity));
        deployDescParams.put("service_name", checkIfMandatory(component.getName(), "name", entity));
        deployDescParams.put("version", checkIfMandatory(component.getVersion(), "version", entity));
        populateOptionalParam(deployDescParams, "type", getPropertyValue(component, "type", null, false, entity));


        deployParamsMap.put(component.getName(), deployDescParams);
    }

    private void populateOptionalParam(Map<String, Object> paramsMap, String type, String paramValue) {
        if (paramValue != null) {
            paramsMap.put(type, paramValue);
        }
    }

    private void processImageServiceComponentDeployDescParams(Map<String, Map<String, Object>> deployParamsMap, Component component) {
        Map<String, Object> deployDescParams = new TreeMap<>();
        String entity = "service:" + component.getName();
        if (CollectionUtils.isNotEmpty(component.getComponents())) {
            for (Component subComponent : component.getComponents()) {
                entity = "sub component '" + subComponent.getName() + "' of service:" + component.getName();
                if (subComponent.getMimeType().equalsIgnoreCase("application/vnd.docker.image")) {
                    deployDescParams.put("docker_digest", checkIfMandatory(CollectionUtils.isNotEmpty(subComponent.getHashes()) ? subComponent.getHashes().get(0).getValue() : "", "hashes", entity));
                    deployDescParams.put("docker_repository_name", checkIfMandatory(subComponent.getGroup(), "group", entity));
                    deployDescParams.put("docker_tag", checkIfMandatory(subComponent.getVersion(), "version", entity));
                    deployDescParams.put("image_name", checkIfMandatory(subComponent.getName(), "name", entity));
                }
            }
        }
        deployDescParams.put("deploy_param", getPropertyValue(component, "deploy_param", "", true, entity));
        deployDescParams.put("artifacts", new ArrayList<>());
        deployDescParams.put("docker_registry", getPropertyValue(component, "docker_registry", null, true, entity));
        deployDescParams.put("full_image_name", getPropertyValue(component, "full_image_name", null, true, entity));
        deployDescParams.put("git_branch", getPropertyValue(component, "git_branch", null, true, entity));
        deployDescParams.put("git_revision", getPropertyValue(component, "git_revision", null, true, entity));
        deployDescParams.put("git_url", getPropertyValue(component, "git_url", null, true, entity));
        deployDescParams.put("image", getPropertyValue(component, "full_image_name", null, true, entity));
        deployDescParams.put("image_type", getPropertyValue(component, "image_type", null, true, entity));
        deployDescParams.put("name", checkIfMandatory(component.getName(), "name", entity));
        deployDescParams.put("promote_artifacts", getPropertyValue(component, "promote_artifacts", null, true, entity));
        deployDescParams.put("qualifier", getPropertyValue(component, "qualifier", null, true, entity));
        deployDescParams.put("version", checkIfMandatory(component.getVersion(), "version", entity));

        deployParamsMap.put(component.getName(), deployDescParams);
    }

    private String getPropertyValue(Component component, String propertyName, String defaultValue, boolean mandatory, String entity) {
        String result = component.getProperties().stream()
                .filter(property -> propertyName.equals(property.getName()))
                .map(Property::getValue)
                .findFirst()
                .orElse(null);
        if (mandatory && result == null) {
            result = defaultValue;
            return checkIfMandatory(result, propertyName, entity);
        }
        return result;
    }

    private String checkIfMandatory(String value, String propertyName, String entity) {
        if (value == null) {
            throw new MandatoryParameterException(String.format("Mandatory Parameter '%s' is not present in '%s'.", propertyName, entity));
        }
        return value;
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

    private void validateAppChart(EntitiesMap entitiesMap, List<Component> components) {
        Optional<Component> optional = components.stream().filter(key -> "application/vnd.qubership.app.chart".equalsIgnoreCase(key.getMimeType())).findAny();
        if (sharedData.isAppChartValidation() && !optional.isPresent()) {
            throw new AppChartValidationException("Failed to process effective set as appchart validation is mandatory " +
                    "and the applicable mime type application/vnd.qubership.app.chart is not found");
        } else if (optional.isPresent()) {
            entitiesMap.setAppChartName(optional.get().getName());
        }
    }

    private void processConfigServiceComponent(Map<String, Map<String, Object>> serviceMap, Component component, String appName, String baseline, Profile override, Bom bomContent) {
        Map<String, Object> profileValues = new TreeMap<>();
        Map<String, Object> serviceParams = new TreeMap<>();
        String entity = "service:" + component.getName();
        serviceParams.put("ARTIFACT_DESCRIPTOR_VERSION", checkIfMandatory(bomContent.getMetadata().getComponent().getVersion(), "version in metadata", entity));
        serviceParams.put("DEPLOYMENT_RESOURCE_NAME", checkIfMandatory(component.getName(), "name", entity) + "-v1");
        serviceParams.put("DEPLOYMENT_VERSION", "v1");
        serviceParams.put("SERVICE_NAME", checkIfMandatory(component.getName(), "name", entity));


        if (CollectionUtils.isNotEmpty(component.getComponents())) {
            for (Component subComponent : component.getComponents()) {
                if (subComponent.getMimeType().equalsIgnoreCase("application/vnd.qubership.resource-profile-baseline")) {
                    profileValues = extractProfileValues(subComponent, appName, component.getName(), override, baseline);
                }
            }
        }

        if (MapUtils.isNotEmpty(profileValues)) {
            serviceParams.putAll(profileValues);
        }
        serviceMap.put(component.getName(), serviceParams);
    }

    private void processImageServiceComponent(Map<String, Map<String, Object>> serviceMap, Component component, String appName, String baseline, Profile override, Bom bomContent) {
        Map<String, Object> profileValues = new TreeMap<>();
        Map<String, Object> serviceParams = new TreeMap<>();
        String tag = null;
        String entity = "service:" + component.getName();
        serviceParams.put("ARTIFACT_DESCRIPTOR_VERSION", checkIfMandatory(bomContent.getMetadata().getComponent().getVersion(), "version in metadata", entity));
        serviceParams.put("DEPLOYMENT_RESOURCE_NAME", checkIfMandatory(component.getName(), "name", entity) + "-v1");
        serviceParams.put("DEPLOYMENT_VERSION", "v1");
        serviceParams.put("SERVICE_NAME", checkIfMandatory(component.getName(), "name", entity));
        String dockerTag = getPropertyValue(component, "full_image_name", null, true, entity);
        serviceParams.put("DOCKER_TAG", dockerTag);
        serviceParams.put("IMAGE_REPOSITORY", getImageRepository(dockerTag));
        addImageParameters(component, serviceParams);

        if (CollectionUtils.isNotEmpty(component.getComponents())) {
            for (Component subComponent : component.getComponents()) {
                if (subComponent.getMimeType().equalsIgnoreCase("application/vnd.docker.image")) {
                    tag = subComponent.getVersion();
                } else if (subComponent.getMimeType().equalsIgnoreCase("application/vnd.qubership.resource-profile-baseline")) {
                    profileValues = extractProfileValues(subComponent, appName, component.getName(), override, baseline);
                }
            }
            serviceParams.put("TAG", checkIfMandatory(tag, "TAG", entity));
        }
        if (MapUtils.isNotEmpty(profileValues)) {
            serviceParams.putAll(profileValues);
        }
        serviceMap.put(component.getName(), serviceParams);
    }

    private void addImageParameters(Component component, Map<String, Object> serviceParams) {
        if (component.getMimeType().equalsIgnoreCase(APPLICATION_OCTET_STREAM)) {
            String key = getPropertyValue(component, "deploy_param", null, false, component.getName());
            if (StringUtils.isNotEmpty(key)) {
                String value = getPropertyValue(component, "full_image_name", null, false, component.getName());
                serviceParams.put(key, value);
            }
        }
    }

    private String getImageRepository(String dockerTag) {
        if (StringUtils.isNotEmpty(dockerTag)) {
            return dockerTag.substring(0, dockerTag.lastIndexOf(":"));
        }
        return null;
    }

    private Map<String, Object> extractProfileValues(Component dataComponent, String appName, String serviceName,
                                                     Profile overrideProfile, String baseline) {
        Map<String, Object> profileValues = new TreeMap<>();
        if (baseline == null) {
            profileService.setOverrideProfiles(appName, serviceName, overrideProfile, profileValues);
        }
        for (ComponentData data : dataComponent.getData()) {
            if (baseline != null && baseline.equals(data.getName().split("\\.")[0])) {
                Content content = data.getContents();
                String encodedText = content.getAttachment().getText();
                profileValues = fileDataConverter.decodeAndParse(encodedText, new TypeReference<TreeMap<String, Object>>() {
                });

                profileService.setOverrideProfiles(appName, serviceName, overrideProfile, profileValues);
                break;
            }
        }
        return profileValues;
    }
}
