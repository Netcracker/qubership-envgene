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
import org.qubership.cloud.devops.commons.utils.Parameter;
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
    private static final String  ENVGENE_DEFAULT = "envgene default";
    private static final String  ENVGENE_PIPELINE_PARAMETER =  "envgene pipeline parameter";
    private static final String  ENVGENE_CALCULATED = "envgene calculated";
    private String baselineOrigin = "sbom, resource-profile-baseline: ";
    String overrideOrigin ="resource-profile-override: ";
    boolean isBaselineOriginSet = false;
    boolean isOverrideOriginSet= false;

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
        if( !isBaselineOriginSet )
        { baselineOrigin = baselineOrigin + baseline;
            isBaselineOriginSet = true;
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

                validateAppChart(entitiesMap, bomContent.getComponents(), appName, appFileRef);

                getPerServiceEntities(entitiesMap, bomContent.getComponents(), appName, baseline, override, bomContent);

                populateEntityDeployDescParams(entitiesMap, bomContent.getComponents(), bomContent);

                if (applicationBomDto != null) {
                    applicationBomDto.setServices(entitiesMap.getServiceMap());
                    applicationBomDto.setDeployerSessionId(entitiesMap.getDeployerSessionId());
                    applicationBomDto.setPerServiceParams(entitiesMap.getPerServiceParams());
                    applicationBomDto.setDeployDescriptors(entitiesMap.getDeployDescParamsMap());
                    applicationBomDto.setCommonDeployDescriptors(entitiesMap.getCommonParamsMap());
                    applicationBomDto.setAppChartName(entitiesMap.getAppChartName());
                    applicationBomDto.setDeployParams(entitiesMap.getDeployParams());
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
        String appName = bomContent.getMetadata().getComponent().getName();
        commonParamsMap.put("APPLICATION_NAME", new Parameter(appName, baselineOrigin, false));
        commonParamsMap.put("MANAGED_BY", new Parameter("argocd", ENVGENE_DEFAULT, false));
        if (StringUtils.isNotEmpty(sharedData.getDeploymentSessionId())) {
            commonParamsMap.put("DEPLOYMENT_SESSION_ID", new Parameter(sharedData.getDeploymentSessionId(), ENVGENE_PIPELINE_PARAMETER, false));
            entitiesMap.setDeployerSessionId(sharedData.getDeploymentSessionId());
        } else {
            String deployerSessionId = UUID.randomUUID().toString();
            commonParamsMap.put("DEPLOYMENT_SESSION_ID", new Parameter(deployerSessionId, ENVGENE_CALCULATED, false));
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
        List<Object> artifacts = new ArrayList<>();
        Map<String, Object> tArtifactMap = new TreeMap<>();
        if (CollectionUtils.isNotEmpty(component.getComponents())) {
            for (Component subComponent : component.getComponents()) {
                entity = "sub component '" + subComponent.getName() + "' of service:" + component.getName();
                if (subComponent.getMimeType().equalsIgnoreCase(serviceArtifactType.getArtifactMimeType())) {
                    primaryArtifactMap.put("artifactId", new Parameter(subComponent.getName(), baselineOrigin, false));
                    primaryArtifactMap.put("groupId", new Parameter(subComponent.getGroup(), baselineOrigin, false));
                    primaryArtifactMap.put("version", new Parameter(subComponent.getVersion(), baselineOrigin, false));
                }
                if (SUB_SERVICE_ARTIFACT_MIME_TYPES.contains(subComponent.getMimeType())) {
                    String name = checkIfMandatory(subComponent.getName(), "name", entity);
                    String version = checkIfMandatory(subComponent.getVersion(), "version", entity);
                    Map<String, Object> artifactMap = new TreeMap<>();
                    artifactMap.put("artifact_id", new Parameter("", baselineOrigin, false));
                    artifactMap.put("artifact_path", new Parameter("", baselineOrigin, false));
                    artifactMap.put("artifact_type", new Parameter("", baselineOrigin, false));
                    Parameter classifierParam = getPropertyValueAsParameter(subComponent, "classifier", null, true, entity, baselineOrigin);
                    if (classifierParam != null) {
                        artifactMap.put("classifier", classifierParam);
                    }
                    artifactMap.put("deploy_params", new Parameter("", baselineOrigin, false));
                    artifactMap.put("gav", new Parameter("", baselineOrigin, false));
                    artifactMap.put("group_id", new Parameter("", baselineOrigin, false));
                    artifactMap.put("id", new Parameter(checkIfMandatory(subComponent.getGroup(), "group", entity) + ":" + name + ":" + version, baselineOrigin, false));
                    String typeValue = getPropertyValue(subComponent, "type", null, true, entity);
                    artifactMap.put("name", new Parameter(name + "-" + version + "." + typeValue, baselineOrigin, false));
                    artifactMap.put("repository", new Parameter("", baselineOrigin, false));
                    artifactMap.put("type", new Parameter(typeValue, baselineOrigin, false));
                    artifactMap.put("url", new Parameter("", baselineOrigin, false));
                    artifactMap.put("version", new Parameter("", baselineOrigin, false));
                    artifacts.add(artifactMap);
                }
                if (APPLICATION_ZIP.equalsIgnoreCase(subComponent.getMimeType())) {
                    String classifier = getPropertyValue(subComponent, "classifier", null, true, entity);
                    String name = subComponent.getName();
                    String version = subComponent.getVersion();
                    if (StringUtils.isNotBlank(classifier)) {
                        tArtifactMap.put(classifier, new Parameter(name + "-" + version + "-" + classifier + ".zip", baselineOrigin, false));
                    } else {
                        tArtifactMap.put("ecl", new Parameter(name + "-" + version + ".zip", baselineOrigin, false));
                    }
                }
            }
        }
        deployDescParams.put("tArtifactNames", tArtifactMap);
        deployDescParams.put("artifact", primaryArtifactMap);
        deployDescParams.put("artifacts", artifacts);
        deployDescParams.put("build_id_dtrust", getPropertyValueAsParameter(component, "build_id_dtrust", null, true, entity, baselineOrigin));
        deployDescParams.put("git_branch", getPropertyValueAsParameter(component, "git_branch", null, true, entity, baselineOrigin));
        deployDescParams.put("git_revision", getPropertyValueAsParameter(component, "git_revision", null, true, entity, baselineOrigin));
        deployDescParams.put("git_url", getPropertyValueAsParameter(component, "git_url", null, true, entity, baselineOrigin));
        deployDescParams.put("maven_repository", getPropertyValueAsParameter(component, "maven_repository", null, true, entity, baselineOrigin));
        deployDescParams.put("name", checkIfMandatoryAsParameter(component.getName(), "name", entity, baselineOrigin));
        deployDescParams.put("service_name", checkIfMandatoryAsParameter(component.getName(), "name", entity, baselineOrigin));
        deployDescParams.put("version", checkIfMandatoryAsParameter(component.getVersion(), "version", entity, baselineOrigin));
        String typeValue = getPropertyValue(component, "type", null, false, entity);
        if (typeValue != null) {
            deployDescParams.put("type", new Parameter(typeValue, baselineOrigin, false));
        }

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
                    String hashValue = CollectionUtils.isNotEmpty(subComponent.getHashes()) ? subComponent.getHashes().get(0).getValue() : "";
                    deployDescParams.put("docker_digest", checkIfMandatoryAsParameter(hashValue, "hashes", entity, baselineOrigin));
                    deployDescParams.put("docker_repository_name", checkIfMandatoryAsParameter(subComponent.getGroup(), "group", entity, baselineOrigin));
                    deployDescParams.put("docker_tag", checkIfMandatoryAsParameter(subComponent.getVersion(), "version", entity, baselineOrigin));
                    deployDescParams.put("image_name", checkIfMandatoryAsParameter(subComponent.getName(), "name", entity, baselineOrigin));
                }
            }
        }
        deployDescParams.put("deploy_param", getPropertyValueAsParameter(component, "deploy_param", "", true, entity, baselineOrigin));
        deployDescParams.put("artifacts", new ArrayList<>());
        deployDescParams.put("docker_registry", getPropertyValueAsParameter(component, "docker_registry", null, true, entity, baselineOrigin));
        Parameter fullImageNameParam = getPropertyValueAsParameter(component, "full_image_name", null, true, entity, baselineOrigin);
        deployDescParams.put("full_image_name", fullImageNameParam);
        deployDescParams.put("image", fullImageNameParam);
        deployDescParams.put("git_branch", getPropertyValueAsParameter(component, "git_branch", null, true, entity, baselineOrigin));
        deployDescParams.put("git_revision", getPropertyValueAsParameter(component, "git_revision", null, true, entity, baselineOrigin));
        deployDescParams.put("git_url", getPropertyValueAsParameter(component, "git_url", null, true, entity, baselineOrigin));
        deployDescParams.put("image_type", getPropertyValueAsParameter(component, "image_type", null, true, entity, baselineOrigin));
        deployDescParams.put("name", checkIfMandatoryAsParameter(component.getName(), "name", entity, baselineOrigin));
        deployDescParams.put("promote_artifacts", getPropertyValueAsParameter(component, "promote_artifacts", null, true, entity, baselineOrigin));
        deployDescParams.put("qualifier", getPropertyValueAsParameter(component, "qualifier", null, true, entity, baselineOrigin));
        deployDescParams.put("version", checkIfMandatoryAsParameter(component.getVersion(), "version", entity, baselineOrigin));

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

    private Parameter getPropertyValueAsParameter(Component component, String propertyName, String defaultValue, boolean mandatory, String entity, String origin) {
        String value = getPropertyValue(component, propertyName, defaultValue, mandatory, entity);
        return value != null ? new Parameter(value, origin, false) : null;
    }

    private String checkIfMandatory(String value, String propertyName, String entity) {
        if (value == null) {
            throw new MandatoryParameterException(String.format("Mandatory Parameter '%s' is not present in '%s'.", propertyName, entity));
        }
        return value;
    }

    private Parameter checkIfMandatoryAsParameter(String value, String propertyName, String entity, String origin) {
        checkIfMandatory(value, propertyName, entity);
        return new Parameter(value, origin, false);
    }

    private void getPerServiceEntities(EntitiesMap entitiesMap, List<Component> components, String appName, String baseline, Profile override, Bom bomContent) {
        for (Component component : components) {
            if (IMAGE_SERVICE_MIME_TYPES.contains(component.getMimeType())) {
                processImageServiceComponent(entitiesMap, component, appName, baseline, override, bomContent);
            } else if (CONFIG_SERVICE_MIME_TYPES.contains(component.getMimeType())) {
                processConfigServiceComponent(entitiesMap.getPerServiceParams(), component, appName, baseline, override, bomContent);
            }
        }
    }

    private void validateAppChart(EntitiesMap entitiesMap, List<Component> components, String appName, String appFileRef) {
        Optional<Component> optional = components.stream().filter(key -> "application/vnd.qubership.app.chart".equalsIgnoreCase(key.getMimeType())).findAny();
        if (sharedData.isAppChartValidation() && !optional.isPresent()) {
            throw new AppChartValidationException(String.format("App chart validation failed: application \"%s\" from SBOM \"%s\" " +
                    "has no component with mime-type \"application/vnd.qubership.app.chart\"", appName, new File(appFileRef).getName()));
        } else if (optional.isPresent()) {
            entitiesMap.setAppChartName(optional.get().getName());
        }
    }

    private void processConfigServiceComponent(Map<String, Map<String, Object>> serviceMap, Component component, String appName, String baseline, Profile override, Bom bomContent) {
        Map<String, Object> profileValues = new TreeMap<>();
        Map<String, Object> serviceParams = new TreeMap<>();
        String entity = "service:" + component.getName();

        serviceParams.put("ARTIFACT_DESCRIPTOR_VERSION", new Parameter(checkIfMandatory(bomContent.getMetadata().getComponent().getVersion(), "version in metadata", entity), baselineOrigin, false));
        serviceParams.put("DEPLOYMENT_RESOURCE_NAME", new Parameter(checkIfMandatory(component.getName(), "name", entity) + "-v1", baselineOrigin, false));
        serviceParams.put("DEPLOYMENT_VERSION", new Parameter("v1", ENVGENE_DEFAULT, false));
        serviceParams.put("SERVICE_NAME", new Parameter(checkIfMandatory(component.getName(), "name", entity), baselineOrigin, false));
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

    private void processImageServiceComponent(EntitiesMap entitiesMap, Component component, String appName, String baseline, Profile override, Bom bomContent) {
        Map<String, Map<String, Object>> perServiceMap = entitiesMap.getPerServiceParams();
        Map<String, Object> profileValues = new TreeMap<>();
        Map<String, Object> serviceParams = new TreeMap<>();
        String tag = null;
        String entity = "service:" + component.getName();
        String dockerTag = getPropertyValue(component, "full_image_name", null, true, entity);
        Object imageRepository = getImageRepository(dockerTag);

        serviceParams.put("ARTIFACT_DESCRIPTOR_VERSION", new Parameter(checkIfMandatory(bomContent.getMetadata().getComponent().getVersion(), "version in metadata", entity), baselineOrigin, false));
        serviceParams.put("DEPLOYMENT_RESOURCE_NAME", new Parameter(checkIfMandatory(component.getName(), "name", entity) + "-v1", baselineOrigin, false));
        serviceParams.put("DEPLOYMENT_VERSION", new Parameter("v1", baselineOrigin, false));
        serviceParams.put("SERVICE_NAME", new Parameter(checkIfMandatory(component.getName(), "name", entity), baselineOrigin, false));
        serviceParams.put("DOCKER_TAG", new Parameter(dockerTag, baselineOrigin, false));
        if (imageRepository != null) {
            serviceParams.put("IMAGE_REPOSITORY", new Parameter(imageRepository, baselineOrigin, false));
        }
        addImageParameters(component, entitiesMap.getDeployParams());

        if (CollectionUtils.isNotEmpty(component.getComponents())) {
            for (Component subComponent : component.getComponents()) {
                if (subComponent.getMimeType().equalsIgnoreCase("application/vnd.docker.image")) {
                    tag = subComponent.getVersion();
                } else if (subComponent.getMimeType().equalsIgnoreCase("application/vnd.qubership.resource-profile-baseline")) {
                    profileValues = extractProfileValues(subComponent, appName, component.getName(), override, baseline);
                }
            }
            serviceParams.put("TAG", new Parameter(checkIfMandatory(tag, "TAG", entity), baselineOrigin, false));
        }
        if (MapUtils.isNotEmpty(profileValues)) {
            serviceParams.putAll(profileValues);
        }
        perServiceMap.put(component.getName(), serviceParams);
    }

    private void addImageParameters(Component component, Map<String, String> serviceParams) {
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
        if (!isOverrideOriginSet) {
            overrideOrigin = overrideOrigin + overrideProfile.getName();
            isOverrideOriginSet = true;
        }
        if (baseline == null) {
            profileService.setOverrideProfilesWithOrigin(appName, serviceName, overrideProfile, profileValues,overrideOrigin);
        }
        for (ComponentData data : dataComponent.getData()) {
            if (baseline != null && baseline.equals(data.getName().split("\\.")[0])) {
                Content content = data.getContents();
                String encodedText = content.getAttachment().getText();
                profileValues = fileDataConverter.decodeAndParse(encodedText, new TypeReference<TreeMap<String, Object>>() {
                });
                if (MapUtils.isNotEmpty(profileValues)) {
                    wrapPlainMapWithOrigin(profileValues, baselineOrigin);
                }
                profileService.setOverrideProfilesWithOrigin(appName, serviceName, overrideProfile, profileValues, overrideOrigin);
                break;
            }
        }
        return profileValues;
    }


    @SuppressWarnings("unchecked")
    private void wrapPlainMapWithOrigin(Map<String, Object> map, String origin) {
        if (map == null || map.isEmpty()) {
            return;
        }
        for (Map.Entry<String, Object> entry : map.entrySet()) {
            Object value = entry.getValue();
            if (value instanceof Parameter) {
                // Keep the existing parameter as is
            } else if (value instanceof Map) {
                wrapPlainMapWithOrigin((Map<String, Object>) value, origin);
            } else if (value instanceof List) {
                wrapPlainListWithOrigin((List<Object>) value, origin);
            } else {
                entry.setValue(new Parameter(value, origin, false));
            }
        }
    }

    @SuppressWarnings("unchecked")
    private List<Object> wrapPlainListWithOrigin(List<Object> list, String origin) {
        if (list == null || list.isEmpty()) {
            return list;
        }
        for (int i = 0; i < list.size(); i++) {
            Object item = list.get(i);
            if (item instanceof Parameter) {
                // Keep existing Parameter as is
            } else if (item instanceof Map) {
                wrapPlainMapWithOrigin((Map<String, Object>) item, origin);
            } else if (item instanceof List) {
                list.set(i, wrapPlainListWithOrigin((List<Object>) item, origin));
            } else {
                list.set(i, new Parameter(item, origin, false));
            }
        }
        return list;
    }

}
