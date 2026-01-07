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

package org.qubership.cloud.devops.cli.repository.implementation;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.dataformat.yaml.YAMLFactory;
import org.cyclonedx.model.Bom;
import org.qubership.cloud.devops.cli.exceptions.constants.ExceptionMessage;
import org.qubership.cloud.devops.cli.utils.FileSystemUtils;
import org.qubership.cloud.devops.cli.utils.deserializer.BomMixin;
import org.qubership.cloud.devops.commons.exceptions.FileParseException;
import org.qubership.cloud.devops.commons.exceptions.JsonParseException;
import org.qubership.cloud.devops.commons.repository.interfaces.FileDataConverter;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;
import lombok.extern.slf4j.Slf4j;
import org.yaml.snakeyaml.DumperOptions;
import org.yaml.snakeyaml.Yaml;
import org.yaml.snakeyaml.nodes.Node;
import org.yaml.snakeyaml.nodes.Tag;
import org.yaml.snakeyaml.representer.Representer;

import java.io.*;
import java.util.*;
import org.qubership.cloud.devops.commons.utils.Parameter;

import static org.qubership.cloud.devops.commons.utils.ConsoleLogger.logError;


@ApplicationScoped
@Slf4j
public class FileDataConverterImpl implements FileDataConverter {
    public static final String CLEANUPER = "cleanuper";
    
    /**
     * List of file names that should be excluded from inline origin comments.
     * Add any file names here that should not have origin comments added.
     */
    private static final Set<String> EXCLUDED_FILES_FROM_ORIGIN_COMMENTS = Set.of(
        "mapping.yaml"
    );
    
    /**
     * Gets the priority of an origin based on parameter priority rules.
     * Lower number = higher priority (1 is highest priority).
     * Based on the priority order:
     * 1. Resource Profile Override (highest)
     * 2. SBOM Resource Profile Baseline (service level)
     * 3. SBOM other attributes (service level)
     * 4. Calculator-generated (service level)
     * 5-16. Other levels (application, namespace, cloud, tenant, extra params, defaults)
     */
    private int getOriginPriority(String origin) {
        if (origin == null || origin.isEmpty()) {
            return Integer.MAX_VALUE; // Lowest priority
        }
        String lowerOrigin = origin.toLowerCase();
        
        // Priority 1: Resource Profile Override (highest)
        if (lowerOrigin.contains("resource-profile-override") || lowerOrigin.contains("resourceprofileoverride")) {
            return 1;
        }
        
        // Priority 2: SBOM Resource Profile Baseline (service level)
        if (lowerOrigin.contains("resource-profile-baseline") || lowerOrigin.contains("resourceprofilebaseline")) {
            return 2;
        }
        
        // Check level first, then determine if it's SBOM, calculated, or user-defined within that level
        // This ensures correct priority ordering
        
        // Priority 5-7: Application level (check before service level to avoid false matches)
        if (origin.startsWith("Application:") || origin.startsWith("Env/Namespace/App:") || 
            origin.startsWith("Env/Cloud/App:") || lowerOrigin.contains("application:")) {
            if (lowerOrigin.contains("sbom")) {
                return 6; // Priority 6: Application level defined in Application SBOM
            }
            if (lowerOrigin.contains("calculated") || lowerOrigin.contains("envgene calculated")) {
                return 7; // Priority 7: Calculator-generated at the Application level
            }
            return 5; // Priority 5: User-defined at Application level in Environment Instance
        }
        
        // Priority 8-10: Namespace level
        if (origin.startsWith("Env/Namespace:") || lowerOrigin.contains("namespace:")) {
            if (lowerOrigin.contains("sbom")) {
                return 9; // Priority 9: Namespace level defined in Application SBOM
            }
            if (lowerOrigin.contains("calculated") || lowerOrigin.contains("envgene calculated")) {
                return 10; // Priority 10: Calculator-generated at the Namespace level
            }
            return 8; // Priority 8: User-defined at the Namespace level in Environment Instance
        }
        
        // Priority 11-13: Cloud level
        if (origin.startsWith("Env/Cloud:") || lowerOrigin.contains("cloud")) {
            if (lowerOrigin.contains("sbom")) {
                return 12; // Priority 12: Cloud level defined in Application SBOM
            }
            if (lowerOrigin.contains("calculated") || lowerOrigin.contains("envgene calculated")) {
                return 13; // Priority 13: Calculator-generated at the Cloud level
            }
            return 11; // Priority 11: User-defined at the Cloud level in Environment Instance
        }
        
        // Priority 3: SBOM other attributes (service level) - only if not already matched above
        // This must come after level checks to ensure service-level SBOM gets priority 3
        if (lowerOrigin.contains("sbom") && !lowerOrigin.contains("resource-profile-baseline") && 
            !lowerOrigin.contains("resourceprofilebaseline")) {
            return 3; // Priority 3: Service level defined in other Application SBOM attributes
        }
        
        // Priority 4: Calculator-generated at service level
        // Only if not already matched to a specific level above
        if (lowerOrigin.equals("envgene calculated") || 
            (lowerOrigin.contains("calculated") && !lowerOrigin.contains("application") && 
             !lowerOrigin.contains("namespace") && !lowerOrigin.contains("cloud") && !lowerOrigin.contains("tenant"))) {
            return 4; // Priority 4: Calculator-generated at the Service level
        }
        
        // Priority 14: Tenant level
        if (origin.startsWith("Env/Tenant:") || lowerOrigin.contains("tenant")) {
            return 14; // Priority 14: User-defined at the Tenant level in Environment Instance
        }
        
        // Priority 15: Calculator extra parameters
        if (lowerOrigin.contains("pipeline parameter") || lowerOrigin.contains("extra_params") || 
            lowerOrigin.contains("extra-params") || lowerOrigin.contains("envgene pipeline parameter")) {
            return 15; // Priority 15: Calculator extra parameters (--extra_params)
        }
        
        // Priority 16: Default values (lowest)
        if (lowerOrigin.contains("envgene default") || lowerOrigin.equals("default")) {
            return 16; // Priority 16: Default values by calculator
        }
        
        // For unknown origins, assign a medium-low priority
        return 20;
    }
    
    /**
     * Compares two origins and returns the one with higher priority (lower priority number).
     * Returns the existing origin if priorities are equal or if new origin is null/empty.
     */
    private String selectHigherPriorityOrigin(String existingOrigin, String newOrigin) {
        if (newOrigin == null || newOrigin.isEmpty()) {
            return existingOrigin;
        }
        if (existingOrigin == null || existingOrigin.isEmpty()) {
            return newOrigin;
        }
        
        int existingPriority = getOriginPriority(existingOrigin);
        int newPriority = getOriginPriority(newOrigin);
        
        // Lower priority number = higher priority, so return the one with lower number
        if (newPriority < existingPriority) {
            return newOrigin;
        } else if (newPriority > existingPriority) {
            return existingOrigin;
        } else {
            // Same priority, keep existing (first one encountered)
            return existingOrigin;
        }
    }
    
    private final ObjectMapper objectMapper;
    private final FileSystemUtils fileSystemUtils;

    @Inject
    public FileDataConverterImpl(FileSystemUtils fileSystemUtils) {
        this.fileSystemUtils = fileSystemUtils;
        this.objectMapper = new ObjectMapper(new YAMLFactory());
    }

    @Override
    public <T> T parseInputFile(Class<T> type, File file) {
        try (InputStream inputStream = new FileInputStream(file)) {
            return objectMapper.readValue(inputStream, type);
        } catch (IOException | IllegalArgumentException e) {
            logError(String.format(ExceptionMessage.FILE_READ_ERROR, file.getAbsolutePath(), e.getMessage()));
            return null;
        }
    }

    @Override
    public Bom parseSbomFile(File file) {
        try {
            ObjectMapper bomMapper = new ObjectMapper();
            bomMapper.addMixIn(Bom.class, BomMixin.class);
            return bomMapper.readValue(file, Bom.class);
        } catch (IOException | IllegalArgumentException e) {
            if (file.getName().startsWith(CLEANUPER) &&
                    e instanceof FileNotFoundException) {
                logError("Issue while reading the file " + e.getMessage());
                return null;
            }
            throw new FileParseException(String.format(ExceptionMessage.FILE_READ_ERROR, file.getAbsolutePath(), e.getMessage()));
        }
    }


    @Override
    public <T> T parseInputFile(TypeReference<T> typeReference, File file) {
        try (InputStream inputStream = new FileInputStream(file)) {
            return objectMapper.readValue(inputStream, typeReference);
        } catch (IOException | IllegalArgumentException e) {
            logError(String.format(ExceptionMessage.FILE_READ_ERROR, file.getAbsolutePath(), e.getMessage()));
            return null;
        }
    }

    @Override
    public void writeToFile(Map<String, Object> params, String... args) throws IOException {
        File file = fileSystemUtils.getFileFromGivenPath(args);
        // Check if this file should be excluded from origin comments
        boolean shouldSkipOriginComments = EXCLUDED_FILES_FROM_ORIGIN_COMMENTS.contains(file.getName());
        
        try (StringWriter stringWriter = new StringWriter();
             BufferedWriter writer = new BufferedWriter(new FileWriter(file))) {
            if (params != null && !params.isEmpty()) {
                // Unwrap Parameter objects and build origin map for comments
                Map<String, Object> unwrappedParams = unwrapValuesWithOrigin(params);
                Map<String, String> originMap = extractOriginMap(params);
                
                getYamlObject().dump(unwrappedParams, stringWriter);
                String yamlContent;
                if (shouldSkipOriginComments) {
                    // Skip adding origin comments for excluded files
                    yamlContent = stringWriter.toString();
                } else {
                    // Add origin comments for all other YAML files
                    yamlContent = addInlineComments(stringWriter.toString(), originMap);
                }
                writer.write(yamlContent);
            }
        }
    }

    private Map<String, Object> unwrapValuesWithOrigin(Map<String, Object> params) {
        Map<String, Object> unwrapped = new TreeMap<>();
        for (Map.Entry<String, Object> entry : params.entrySet()) {
            Object value = entry.getValue();
            if (value instanceof Parameter) {
                unwrapped.put(entry.getKey(), unwrapValue(((Parameter) value).getValue()));
            } else {
                unwrapped.put(entry.getKey(), unwrapValue(value));
            }
        }
        return unwrapped;
    }
    
    private Object unwrapValue(Object value) {
        if (value == null) {
            return null;
        }
        if (value instanceof Parameter) {
            return unwrapValue(((Parameter) value).getValue());
        } else if (value instanceof Map) {
            Map<String, Object> map = (Map<String, Object>) value;
            Map<String, Object> unwrapped = new TreeMap<>();
            for (Map.Entry<String, Object> entry : map.entrySet()) {
                unwrapped.put(entry.getKey(), unwrapValue(entry.getValue()));
            }
            return unwrapped;
        } else if (value instanceof List) {
            List<Object> list = (List<Object>) value;
            List<Object> unwrapped = new java.util.ArrayList<>();
            for (Object item : list) {
                unwrapped.add(unwrapValue(item));
            }
            return unwrapped;
        }
        return value;
    }
    
    private Map<String, String> extractOriginMap(Map<String, Object> params) {
        Map<String, String> originMap = new TreeMap<>();
        for (Map.Entry<String, Object> entry : params.entrySet()) {
            extractOriginMapRecursive(entry.getValue(), originMap, entry.getKey());
        }
        return originMap;
    }
    
    private void extractOriginMapRecursive(Object value, Map<String, String> originMap, String keyPath) {
        if (value == null) {
            return;
        }
        if (value instanceof Parameter) {
            Parameter param = (Parameter) value;
            if (param.getOrigin() != null && !param.getOrigin().isEmpty()) {
                // Store origin for both the full path and the direct key (for spread scenarios)
                // Use priority-based selection: keep the origin with higher priority (lower priority number)
                String existingOrigin = originMap.get(keyPath);
                String selectedOrigin = selectHigherPriorityOrigin(existingOrigin, param.getOrigin());
                originMap.put(keyPath, selectedOrigin);
                
                // Extract the direct key name (last part of path) for nested structures
                if (keyPath.contains(".")) {
                    String directKey = keyPath.substring(keyPath.lastIndexOf('.') + 1);
                    // Use priority-based selection for direct key as well
                    String existingDirectOrigin = originMap.get(directKey);
                    String selectedDirectOrigin = selectHigherPriorityOrigin(existingDirectOrigin, param.getOrigin());
                    originMap.put(directKey, selectedDirectOrigin);
                }
            }
            extractOriginMapRecursive(param.getValue(), originMap, keyPath);
        } else if (value instanceof Map) {
            Map<String, Object> map = (Map<String, Object>) value;
            for (Map.Entry<String, Object> entry : map.entrySet()) {
                if (entry.getKey() != null) {
                    String nestedKey = keyPath + "." + entry.getKey();
                    extractOriginMapRecursive(entry.getValue(), originMap, nestedKey);
                }
            }
        } else if (value instanceof List) {
            List<Object> list = (List<Object>) value;
            for (int i = 0; i < list.size(); i++) {
                String nestedKey = keyPath + "[" + i + "]";
                extractOriginMapRecursive(list.get(i), originMap, nestedKey);
            }
        }
    }

    /**
     * Converts origin strings to standardized comment formats based on the mapping table.
     * 
     * @param origin The original origin string (e.g., "Env/Tenant: tenant-name", "Application: app-name")
     * @return The standardized comment format (e.g., "# tenant", "# application: app-name")
     */
    private String convertOriginToComment(String origin) {
        if (origin == null || origin.isEmpty()) {
            return origin;
        }
        
        // If already in comment format (starts with "#"), return as-is
        String trimmedOrigin = origin.trim();
        if (trimmedOrigin.startsWith("#")) {
            return trimmedOrigin;
        }
        
        // Environment Instance, Tenant (including E2E and config-server variants)
        if (origin.startsWith("Env/Tenant:")) {
            // Extract tenant name from "Env/Tenant: <tenant-name>"
            String tenantName = origin.substring("Env/Tenant:".length()).trim();
            if (!tenantName.isEmpty()) {
                return "# tenant: " + tenantName;
            }
            return "# tenant";
        }
        if (origin.startsWith("Env/Tenant/e2e:") || origin.startsWith("Env/Tenant/E2E:")) {
            // Extract tenant name from "Env/Tenant/e2e: <tenant-name>"
            String tenantName = origin.substring(origin.indexOf(":") + 1).trim();
            if (!tenantName.isEmpty()) {
                return "# tenant: " + tenantName;
            }
            return "# tenant";
        }
        if (origin.startsWith("Env/Tenant/config-server:")) {
            // Extract tenant name from "Env/Tenant/config-server: <tenant-name>"
            String tenantName = origin.substring("Env/Tenant/config-server:".length()).trim();
            if (!tenantName.isEmpty()) {
                return "# tenant: " + tenantName;
            }
            return "# tenant";
        }
        
        // Environment Instance, Cloud (including E2E and config-server variants)
        if (origin.startsWith("Env/Cloud:")) {
            // Extract cloud name from "Env/Cloud: <tenant-name>/<cloud-name>" or "Env/Cloud:<tenant-name>/<cloud-name>"
            String afterColon = origin.substring("Env/Cloud:".length()).trim();
            if (!afterColon.isEmpty()) {
                String[] parts = afterColon.split("/");
                if (parts.length >= 2) {
                    // Format: "tenant/cloud" - extract cloud name (second part)
                    String cloudName = parts[1].trim();
                    if (!cloudName.isEmpty()) {
                        return "# cloud: " + cloudName;
                    }
                } else if (parts.length == 1 && !parts[0].isEmpty()) {
                    // Fallback: if only one part, use it as cloud name
                    return "# cloud: " + parts[0].trim();
                }
            }
            return "# cloud";
        }
        if (origin.startsWith("Env/Cloud/e2e:") || origin.startsWith("Env/Cloud/E2E:")) {
            // Extract cloud name from "Env/Cloud/e2e: <tenant-name>/<cloud-name>"
            String afterColon = origin.substring(origin.indexOf(":") + 1).trim();
            if (!afterColon.isEmpty()) {
                String[] parts = afterColon.split("/");
                if (parts.length >= 2) {
                    String cloudName = parts[1].trim();
                    if (!cloudName.isEmpty()) {
                        return "# cloud: " + cloudName;
                    }
                } else if (parts.length == 1 && !parts[0].isEmpty()) {
                    return "# cloud: " + parts[0].trim();
                }
            }
            return "# cloud";
        }
        if (origin.startsWith("Env/Cloud/config-server:")) {
            // Extract cloud name from "Env/Cloud/config-server: <tenant-name>/<cloud-name>"
            String afterColon = origin.substring("Env/Cloud/config-server:".length()).trim();
            if (!afterColon.isEmpty()) {
                String[] parts = afterColon.split("/");
                if (parts.length >= 2) {
                    String cloudName = parts[1].trim();
                    if (!cloudName.isEmpty()) {
                        return "# cloud: " + cloudName;
                    }
                } else if (parts.length == 1 && !parts[0].isEmpty()) {
                    return "# cloud: " + parts[0].trim();
                }
            }
            return "# cloud";
        }
        
        // Environment Instance, Namespace (including E2E and config-server variants)
        if (origin.startsWith("Env/Namespace:")) {
            // Extract namespace name from "Env/Namespace: tenant/cloud/namespace"
            String[] parts = origin.substring("Env/Namespace:".length()).trim().split("/");
            if (parts.length >= 3) {
                return "# namespace: " + parts[2];
            }
            return "# namespace";
        }
        if (origin.startsWith("Env/Namespace/e2e:") || origin.startsWith("Env/Namespace/E2E:")) {
            String[] parts = origin.substring(origin.indexOf(":") + 1).trim().split("/");
            if (parts.length >= 3) {
                return "# namespace: " + parts[2];
            }
            return "# namespace";
        }
        if (origin.startsWith("Env/Namespace/config-server:")) {
            String[] parts = origin.substring("Env/Namespace/config-server:".length()).trim().split("/");
            if (parts.length >= 3) {
                return "# namespace: " + parts[2];
            }
            return "# namespace";
        }
        
        // Environment Instance, Application (including config-server variants)
        if (origin.startsWith("Env/Namespace/App:")) {
            // Extract app name from "Env/Namespace/App: tenant/cloud/namespace/app"
            String[] parts = origin.substring("Env/Namespace/App:".length()).trim().split("/");
            if (parts.length >= 4) {
                return "# application: " + parts[3];
            }
            return "# application";
        }
        if (origin.startsWith("Env/Cloud/App:")) {
            // Extract app name from "Env/Cloud/App: tenant/cloud/app"
            String[] parts = origin.substring("Env/Cloud/App:".length()).trim().split("/");
            if (parts.length >= 3) {
                return "# application: " + parts[2];
            }
            return "# application";
        }
        if (origin.startsWith("Env/Namespace/App/config-server:")) {
            String[] parts = origin.substring("Env/Namespace/App/config-server:".length()).trim().split("/");
            if (parts.length >= 4) {
                return "# application: " + parts[3];
            }
            return "# application";
        }
        if (origin.startsWith("Env/Cloud/App/config-server:")) {
            String[] parts = origin.substring("Env/Cloud/App/config-server:".length()).trim().split("/");
            if (parts.length >= 3) {
                return "# application: " + parts[2];
            }
            return "# application";
        }
        
        if (origin.startsWith("Application:")) {
            String appName = origin.substring("Application:".length()).trim();
            return "# application: " + appName;
        }
        
        // Resource Profile Override
        if (origin.contains("resource-profile-override") || origin.contains("ResourceProfileOverride")) {
            // Try to extract profile name if available
            if (origin.contains(":")) {
                String profileName = origin.substring(origin.lastIndexOf(":") + 1).trim();
                if (!profileName.isEmpty()) {
                    return "# resource-profile-override: " + profileName;
                }
            }
            return "# resource-profile-override";
        }
        
        // Environment Instance, Composite Structure
        if (origin.contains("composite-structure") || origin.equals("composite_structure.yaml") || 
            origin.equals("composite-structure")) {
            return "# composite-structure";
        }
        
        // Environment Instance, BG Domain
        if (origin.contains("bg-domain") || origin.equals("bg-domain.yaml") || 
            origin.equals("bg-domain")) {
            return "# bg-domain";
        }
        
        // Application SBOM
        if (origin.contains("SBOM") || origin.equals("sbom") || origin.startsWith("SBOM:") || origin.startsWith("sbom:")) {
            // Check if it's a resource profile baseline
            // Support formats like: "sbom:resource-profile-baseline:dev", "sbom,resource-profile-baseline:dev", 
            // "SBOM:resource-profile-baseline:dev", or contains "resource-profile-baseline"
            if (origin.contains("resource-profile-baseline") || origin.contains("ResourceProfileBaseline")) {
                // Try to extract baseline name
                String baselineName = null;
                
                // Try format: "sbom:resource-profile-baseline:dev" or "sbom,resource-profile-baseline:dev"
                if (origin.contains("resource-profile-baseline:")) {
                    baselineName = origin.substring(origin.indexOf("resource-profile-baseline:") + "resource-profile-baseline:".length()).trim();
                } else if (origin.contains("ResourceProfileBaseline:")) {
                    baselineName = origin.substring(origin.indexOf("ResourceProfileBaseline:") + "ResourceProfileBaseline:".length()).trim();
                } else if (origin.contains(":")) {
                    // Fallback: extract after last colon
                    baselineName = origin.substring(origin.lastIndexOf(":") + 1).trim();
                }
                
                // Clean up baseline name (remove any path separators or extra info)
                if (baselineName != null) {
                    if (baselineName.contains("/")) {
                        baselineName = baselineName.substring(baselineName.lastIndexOf("/") + 1);
                    }
                    if (baselineName.contains(",")) {
                        baselineName = baselineName.split(",")[0].trim();
                    }
                    if (!baselineName.isEmpty()) {
                        return "# sbom, resource-profile-baseline: " + baselineName;
                    }
                }
                // If we couldn't extract baseline name but it's clearly a baseline, return generic format
                return "# sbom, resource-profile-baseline";
            }
            return "# sbom";
        }
        
        // Calculated by calculator
        if (origin.contains("calculated") || origin.contains("Calculated") || 
            origin.contains("envgene calculated") || origin.equals("envgene calculated")) {
            return "# envgene calculated";
        }
        
        // Calculator --extra_params
        if (origin.contains("pipeline parameter") || origin.contains("extra_params") || 
            origin.contains("extra-params") || origin.startsWith("consumer/")) {
            return "# envgene pipeline parameter";
        }
        
        // Default value by calculator
        if (origin.contains("default") || origin.contains("Default") || 
            origin.contains("envgene default") || origin.equals("envgene default")) {
            return "# envgene default";
        }
        
        // Parameter Set origins (Params/Tenant, Params/Cloud, Params/Namespace, etc.)
        if (origin.startsWith("Params/Tenant:")) {
            // Extract tenant name from "Params/Tenant: <tenant-name>/<param-set-name>"
            String[] parts = origin.substring("Params/Tenant:".length()).trim().split("/");
            if (parts.length >= 1 && !parts[0].isEmpty()) {
                return "# tenant: " + parts[0];
            }
            return "# tenant";
        }
        if (origin.startsWith("Params/Cloud:")) {
            // Extract cloud name from "Params/Cloud: <tenant-name>/<cloud-name>/<param-set-name>"
            String afterColon = origin.substring("Params/Cloud:".length()).trim();
            if (!afterColon.isEmpty()) {
                String[] parts = afterColon.split("/");
                if (parts.length >= 2) {
                    // Format: "tenant/cloud/param-set" - extract cloud name (second part)
                    String cloudName = parts[1].trim();
                    if (!cloudName.isEmpty()) {
                        return "# cloud: " + cloudName;
                    }
                } else if (parts.length == 1 && !parts[0].isEmpty()) {
                    return "# cloud: " + parts[0].trim();
                }
            }
            return "# cloud";
        }
        if (origin.startsWith("Params/Namespace:")) {
            // Extract namespace name from "Params/Namespace: tenant/cloud/namespace/app"
            String[] parts = origin.substring("Params/Namespace:".length()).trim().split("/");
            if (parts.length >= 3) {
                return "# namespace: " + parts[2];
            }
            return "# namespace";
        }
        if (origin.startsWith("Params/App:") || origin.startsWith("Params/Cloud/Apps:") || 
            origin.startsWith("Params/Namespace/Apps:")) {
            // Extract app name if available
            String[] parts = origin.substring(origin.indexOf(":") + 1).trim().split("/");
            if (parts.length >= 4) {
                return "# application: " + parts[3];
            } else if (parts.length >= 2) {
                return "# application: " + parts[1];
            }
            return "# application";
        }
        if (origin.startsWith("Params:")) {
            // Generic parameter set
            String value = origin.substring("Params:".length()).trim();
            if (!value.isEmpty()) {
                return "# " + value;
            }
            return "# parameter-set";
        }
        
        // Custom parameters
        if (origin.equals("Custom") || origin.equals("CUSTOM_PARAMS_ORIGIN")) {
            return "# envgene calculated";
        }
        
        // Fallback: Handle cloud origins that don't match specific patterns
        // Check if it's a cloud-level origin (but not already matched above)
        String lowerOrigin = origin.toLowerCase();
        if (lowerOrigin.contains("cloud") && !lowerOrigin.contains("application") && 
            !lowerOrigin.contains("namespace") && !lowerOrigin.contains("tenant") &&
            !lowerOrigin.contains("sbom") && !lowerOrigin.contains("calculated")) {
            // Try to extract cloud name from various formats
            if (origin.contains(":")) {
                String[] parts = origin.split(":");
                if (parts.length >= 2) {
                    String valuePart = parts[parts.length - 1].trim();
                    if (valuePart.contains("/")) {
                        // Format: "Env/Cloud: tenant/cloud" or similar
                        String[] pathParts = valuePart.split("/");
                        if (pathParts.length >= 2) {
                            return "# cloud: " + pathParts[pathParts.length - 1];
                        }
                    } else if (!valuePart.isEmpty()) {
                        return "# cloud: " + valuePart;
                    }
                }
            }
            // If we can't extract name, just return generic cloud comment
            return "# cloud";
        }
        
        // Fallback: Handle tenant origins that don't match specific patterns
        if (lowerOrigin.contains("tenant") && !lowerOrigin.contains("application") && 
            !lowerOrigin.contains("namespace") && !lowerOrigin.contains("cloud") &&
            !lowerOrigin.contains("sbom") && !lowerOrigin.contains("calculated")) {
            // Try to extract tenant name
            if (origin.contains(":")) {
                String[] parts = origin.split(":");
                if (parts.length >= 2) {
                    String valuePart = parts[parts.length - 1].trim();
                    if (valuePart.contains("/")) {
                        // Format: "Env/Tenant: tenant" or "Env/Tenant: tenant/..."
                        String[] pathParts = valuePart.split("/");
                        if (pathParts.length >= 1 && !pathParts[0].isEmpty()) {
                            return "# tenant: " + pathParts[0];
                        }
                    } else if (!valuePart.isEmpty()) {
                        return "# tenant: " + valuePart;
                    }
                }
            }
            return "# tenant";
        }
        
        // For other origins, try to preserve meaningful information
        // Remove common prefixes and format nicely
        if (origin.contains(":")) {
            String[] parts = origin.split(":", 2);
            if (parts.length == 2) {
                String prefix = parts[0].trim();
                String value = parts[1].trim();
                
                // For other structured origins, use the value part if meaningful
                if (!value.isEmpty() && !value.contains("/")) {
                    return "# " + value;
                }
            }
        }
        
        // If origin doesn't match any known pattern and contains calculated/derived terms,
        // treat as calculated
        if (lowerOrigin.contains("calc") || lowerOrigin.contains("derive") || 
            lowerOrigin.contains("generate") || lowerOrigin.contains("compute")) {
            return "# envgene calculated";
        }
        
        // Fallback: use origin as-is with # prefix (but limit length to avoid very long comments)
        if (origin.length() > 100) {
            return "# " + origin.substring(0, 97) + "...";
        }
        return "# " + origin;
    }
    
    private String addInlineComments(String yamlContent, Map<String, String> originMap) {
        if (originMap.isEmpty()) {
            return yamlContent;
        }
        
        // Build a map of key names to origins for quick lookup
        // Store both full paths and direct key names, converting origins to comment format
        // For direct keys, use priority-based selection to keep highest priority origin
        Map<String, String> keyNameToOrigin = new TreeMap<>();
        Map<String, String> directKeyToOrigin = new TreeMap<>(); // Track origins for direct keys to compare priorities
        
        for (Map.Entry<String, String> entry : originMap.entrySet()) {
            String fullKey = entry.getKey();
            String origin = entry.getValue();
            String comment = convertOriginToComment(origin);
            
            // Store the full path with converted comment
            keyNameToOrigin.put(fullKey, comment);
            
            // Also store by direct key name (last part of path) for nested structures
            // Use priority-based selection to ensure highest priority origin is kept
            if (fullKey.contains(".")) {
                String directKey = fullKey.substring(fullKey.lastIndexOf('.') + 1);
                String existingDirectOrigin = directKeyToOrigin.get(directKey);
                String selectedOrigin = selectHigherPriorityOrigin(existingDirectOrigin, origin);
                directKeyToOrigin.put(directKey, selectedOrigin);
                keyNameToOrigin.put(directKey, convertOriginToComment(selectedOrigin));
            } else {
                // For direct keys without path, store directly
                directKeyToOrigin.put(fullKey, origin);
            }
        }
        
        // Process YAML line by line, tracking the current path based on indentation
        StringBuilder result = new StringBuilder();
        String[] lines = yamlContent.split("\n", -1);
        java.util.List<String> pathStack = new java.util.ArrayList<>(); // Track current path based on indentation
        java.util.List<Integer> indentStack = new java.util.ArrayList<>(); // Track indentation levels
        java.util.Map<Integer, String> pendingComments = new java.util.HashMap<>(); // Track comments to add to next line (for values on next line)
        
        for (int i = 0; i < lines.length; i++) {
            String line = lines[i];
            String trimmedLine = line.trim();
            
            // Check if there's a pending comment for this line (value on next line case)
            if (pendingComments.containsKey(i)) {
                String comment = pendingComments.remove(i);
                // Add comment after value with single space
                // Find where the value ends (before any existing comment or at end of line)
                int valueEndIndex = line.length();
                if (line.contains("#")) {
                    valueEndIndex = line.indexOf("#");
                    // Trim trailing spaces before existing comment
                    while (valueEndIndex > 0 && line.charAt(valueEndIndex - 1) == ' ') {
                        valueEndIndex--;
                    }
                } else {
                    // Trim trailing spaces at end of line
                    while (valueEndIndex > 0 && line.charAt(valueEndIndex - 1) == ' ') {
                        valueEndIndex--;
                    }
                }
                String valuePart = line.substring(0, valueEndIndex);
                line = valuePart + " " + comment;
            }
            
            // Skip empty lines and existing comments
            if (trimmedLine.isEmpty() || trimmedLine.startsWith("#")) {
                result.append(line).append("\n");
                continue;
            }
            
            // Skip YAML anchors and aliases on their own lines
            // &id001, *id001, <<: *id001 should be skipped
            // But regular keys with anchor references in values should still be processed
            if (trimmedLine.startsWith("&") || trimmedLine.startsWith("*") || trimmedLine.startsWith("<<:")) {
                result.append(line).append("\n");
                continue;
            }
            
            // Calculate indentation (number of spaces at the start)
            int indent = 0;
            for (int j = 0; j < line.length() && line.charAt(j) == ' '; j++) {
                indent++;
            }
            
            // Update path stack based on indentation
            while (!indentStack.isEmpty() && indentStack.get(indentStack.size() - 1) >= indent) {
                indentStack.remove(indentStack.size() - 1);
                if (!pathStack.isEmpty()) {
                    pathStack.remove(pathStack.size() - 1);
                }
            }
            
            // Check if this line contains a key that has an origin
            if (trimmedLine.contains(":") && !trimmedLine.contains("#")) {
                String keyName = trimmedLine.substring(0, trimmedLine.indexOf(':')).trim();
                
                // Skip if key name is an anchor/alias marker (but allow regular keys that reference anchors)
                if (keyName.equals("&") || keyName.equals("*") || keyName.equals("<<")) {
                    result.append(line).append("\n");
                    continue;
                }
                
                // Build current path
                String currentPath = pathStack.isEmpty() ? keyName : 
                    String.join(".", pathStack) + "." + keyName;
                
                // Try to find origin: first by full path, then by direct key name
                String origin = originMap.get(currentPath);
                String comment = null;
                if (origin != null) {
                    comment = convertOriginToComment(origin);
                } else {
                    comment = keyNameToOrigin.get(keyName);
                }
                
                if (comment != null && !comment.isEmpty()) {
                    // Check if this is a multiline value (| or >)
                    String valuePart = trimmedLine.substring(trimmedLine.indexOf(':') + 1).trim();
                    boolean isMultiline = valuePart.equals("|") || valuePart.equals(">") || 
                                         valuePart.equals("|-") || valuePart.equals(">-") ||
                                         valuePart.equals("|+") || valuePart.equals(">+");
                    
                    if (isMultiline) {
                        // Rule: For multiline values, add comment on the previous line above the parameter
                        // Insert comment before the current line with same indentation
                        String commentLine = line.substring(0, indent) + comment;
                        result.append(commentLine).append("\n");
                        result.append(line).append("\n");
                    } else {
                        // Rule: For non-multiline values, add comment after a single space following the value
                        int colonIndex = line.indexOf(':');
                        String beforeColon = line.substring(0, colonIndex);
                        String afterColon = line.substring(colonIndex + 1);
                        String trimmedAfterColon = afterColon.trim();
                        
                        if (trimmedAfterColon.isEmpty()) {
                            // Value is on next line(s) - store comment to add after the value on next line
                            // Look ahead to find the next non-empty line that's not a comment or anchor
                            int nextLineIndex = i + 1;
                            while (nextLineIndex < lines.length) {
                                String nextLine = lines[nextLineIndex].trim();
                                if (nextLine.isEmpty() || nextLine.startsWith("#") || 
                                    nextLine.startsWith("&") || nextLine.startsWith("*") || nextLine.startsWith("<<")) {
                                    nextLineIndex++;
                                } else {
                                    // Found the line with the value, store comment for that line
                                    pendingComments.put(nextLineIndex, comment);
                                    break;
                                }
                            }
                            result.append(line).append("\n");
                        } else {
                            // Value is on same line, add comment after value with exactly one space
                            // Find where the value ends (before any existing comment or at end of line)
                            int valueEndIndex = afterColon.length();
                            if (afterColon.contains("#")) {
                                valueEndIndex = afterColon.indexOf("#");
                                // Trim trailing spaces before existing comment
                                while (valueEndIndex > 0 && afterColon.charAt(valueEndIndex - 1) == ' ') {
                                    valueEndIndex--;
                                }
                            } else {
                                // Trim trailing spaces at end of line
                                while (valueEndIndex > 0 && afterColon.charAt(valueEndIndex - 1) == ' ') {
                                    valueEndIndex--;
                                }
                            }
                            
                            String valuePart2 = afterColon.substring(0, valueEndIndex);
                            
                            // Rule: Add comment after value with exactly one space (replace existing comment if any)
                            line = beforeColon + ":" + valuePart2 + " " + comment;
                            result.append(line).append("\n");
                        }
                    }
                } else {
                    // No comment, just add the line
                    result.append(line).append("\n");
                }
                
                // Add this key to the path stack if it's a map (not a scalar value on same line)
                // Check if the value is on the same line (scalar) or on next lines (map/list)
                String valuePart = trimmedLine.substring(trimmedLine.indexOf(':') + 1).trim();
                boolean isMapOrList = valuePart.isEmpty() || valuePart.equals("|") || valuePart.equals(">") || 
                                     valuePart.equals("|-") || valuePart.equals(">-") ||
                                     valuePart.equals("|+") || valuePart.equals(">+");
                
                if (isMapOrList) {
                    pathStack.add(keyName);
                    indentStack.add(indent);
                }
            } else {
                // Line doesn't contain a key-value pair, just append it
                result.append(line).append("\n");
            }
        }
        
        return result.toString();
    }


    @Override
    public <T> Map<String, Object> getObjectMap(T inputObject) {
        ObjectMapper objectMapper = new ObjectMapper();
        return objectMapper.convertValue(inputObject, new TypeReference<Map<String, Object>>() {
        });
    }


    private static Yaml getYamlObject() {
        DumperOptions options = new DumperOptions();
        options.setDefaultFlowStyle(DumperOptions.FlowStyle.BLOCK);
        options.setDefaultScalarStyle(DumperOptions.ScalarStyle.PLAIN);
        options.setPrettyFlow(false);
        Representer representer = new Representer(options) {
            @Override
            protected Node representScalar(Tag tag, String value, DumperOptions.ScalarStyle style) {
                if (value.equals("!merge")) {
                    value = "<<";
                    Node node = super.representScalar(tag, value, style);
                    node.setTag(Tag.MERGE);
                    return node;

                } else {
                    return super.representScalar(tag, value, style);
                }
            }


        };
        return new Yaml(representer, options);
    }

    public <T> T decodeAndParse(String encodedText, TypeReference<T> typeReference) {
        try {
            byte[] decoded = Base64.getDecoder().decode(encodedText);
            return objectMapper.readValue(decoded, typeReference);
        } catch (IOException e) {
            throw new JsonParseException("Failed to parse encoded content", e);
        }
    }

    public <T> T decodeAndParse(String encodedText, Class<T> clazz) {
        try {
            byte[] decoded = Base64.getDecoder().decode(encodedText);
            return objectMapper.readValue(decoded, clazz);
        } catch (IOException e) {
            throw new JsonParseException("Failed to parse encoded content", e);
        }
    }


}
