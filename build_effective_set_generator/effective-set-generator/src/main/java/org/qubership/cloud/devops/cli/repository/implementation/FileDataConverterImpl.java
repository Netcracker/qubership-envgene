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
import org.qubership.cloud.devops.cli.pojo.dto.shared.SharedData;
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
    
    // Files excluded from inline origin comments
    private static final Set<String> EXCLUDED_FILES = Set.of("mapping.yaml");
    
    private final ObjectMapper objectMapper;
    private final FileSystemUtils fileSystemUtils;
    private final SharedData sharedData;

    @Inject
    public FileDataConverterImpl(FileSystemUtils fileSystemUtils, SharedData sharedData) {
        this.fileSystemUtils = fileSystemUtils;
        this.sharedData = sharedData;
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
        // Get enableTraceability from SharedData - file writer handles writing based on this
        boolean enableTraceability = sharedData != null && sharedData.isEnableTraceability();
        writeToFileInternal(params, enableTraceability, args);
    }
    
    @Override
    public void writeToFile(Map<String, Object> params, boolean enableTraceability, String... args) throws IOException {
        // This overload is kept for backward compatibility but delegates to internal method
        writeToFileInternal(params, enableTraceability, args);
    }
    
    private void writeToFileInternal(Map<String, Object> params, boolean enableTraceability, String... args) throws IOException {
        File file = fileSystemUtils.getFileFromGivenPath(args);
        boolean shouldSkip = EXCLUDED_FILES.contains(file.getName());
        
        try (StringWriter stringWriter = new StringWriter();
             BufferedWriter writer = new BufferedWriter(new FileWriter(file))) {
            if (params != null && !params.isEmpty()) {
                // Unwrap Parameter objects for YAML dumping
                Map<String, String> originMap = enableTraceability ? new TreeMap<>() : null;
                Map<String, Object> unwrappedParams = unwrapValuesWithOrigin(params, originMap);
                
                getYamlObject().dump(unwrappedParams, stringWriter);
                String yamlContent = stringWriter.toString();
                
                // Add inline comments only if traceability is enabled and file is not excluded
                if (enableTraceability && !shouldSkip && originMap != null && !originMap.isEmpty()) {
                    yamlContent = addInlineComments(yamlContent, originMap);
                }
                
                writer.write(yamlContent);
            }
        }
    }

    private Map<String, Object> unwrapValuesWithOrigin(Map<String, Object> params, Map<String, String> originMap) {
        if (params == null) {
            return null;
        }
        return unwrapParameterMapRecursive(params, originMap, "");
    }
    
    private void storeOrigin(Map<String, String> originMap, String path, String origin) {
        if (originMap != null && origin != null && !origin.isEmpty()) {
            originMap.put(path, origin);
            int lastDot = path.lastIndexOf('.');
            if (lastDot >= 0) {
                originMap.putIfAbsent(path.substring(lastDot + 1), origin);
            }
        }
    }
    
    private Map<String, Object> unwrapParameterMapRecursive(Map<String, Object> map, Map<String, String> originMap, String pathPrefix) {
        if (map == null) return null;
        Map<String, Object> unwrapped = new TreeMap<>();
        for (Map.Entry<String, Object> entry : map.entrySet()) {
            String key = entry.getKey();
            String currentPath = pathPrefix.isEmpty() ? key : pathPrefix + "." + key;
            Object value = entry.getValue();
            
            if (value instanceof Parameter) {
                Parameter param = (Parameter) value;
                if (originMap != null && param.getOrigin() != null && !param.getOrigin().isEmpty()) {
                    originMap.put(currentPath, param.getOrigin());
                    originMap.putIfAbsent(key, param.getOrigin()); // Always store direct key
                }
                unwrapped.put(key, unwrapValueRecursive(param.getValue(), originMap, currentPath));
            } else {
                unwrapped.put(key, unwrapValueRecursive(value, originMap, currentPath));
            }
        }
        return unwrapped;
    }
    
    private Object unwrapValueRecursive(Object value, Map<String, String> originMap, String pathPrefix) {
        if (value == null) return null;
        if (value instanceof Parameter) {
            Parameter param = (Parameter) value;
            storeOrigin(originMap, pathPrefix, param.getOrigin());
            return unwrapValueRecursive(param.getValue(), originMap, pathPrefix);
        }
        if (value instanceof Map) {
            Map<String, Object> map = (Map<String, Object>) value;
            Map<String, Object> unwrapped = new TreeMap<>();
            for (Map.Entry<String, Object> entry : map.entrySet()) {
                String nestedPath = pathPrefix.isEmpty() ? entry.getKey() : pathPrefix + "." + entry.getKey();
                unwrapped.put(entry.getKey(), unwrapValueRecursive(entry.getValue(), originMap, nestedPath));
            }
            return unwrapped;
        }
        if (value instanceof List) {
            List<Object> list = (List<Object>) value;
            List<Object> unwrapped = new ArrayList<>();
            for (int i = 0; i < list.size(); i++) {
                unwrapped.add(unwrapValueRecursive(list.get(i), originMap, pathPrefix + "[" + i + "]"));
            }
            return unwrapped;
        }
        return value;
    }

    // Convert origin to comment format
    private String convertOriginToComment(String origin) {
        if (origin == null || origin.isEmpty() || origin.trim().startsWith("#")) {
            return origin;
        }
        String lower = origin.toLowerCase();
        String name = extractNameAfterColon(origin);
        
        // Pattern matching for common origins
        if (origin.startsWith("Env/Tenant:") || origin.startsWith("Params/Tenant:")) {
            return name != null ? "# tenant: " + name : "# tenant";
        }
        if (origin.startsWith("Env/Cloud:") || origin.startsWith("Params/Cloud:")) {
            String cloudName = extractNameAfterColon(origin, "/", 1);
            return cloudName != null ? "# cloud: " + cloudName : "# cloud";
        }
        if (origin.startsWith("Env/Namespace:") || origin.startsWith("Params/Namespace:")) {
            String nsName = extractNameAfterColon(origin, "/", 2);
            return nsName != null ? "# namespace: " + nsName : "# namespace";
        }
        if (origin.startsWith("Application:") || origin.startsWith("Env/Namespace/App:") || 
            origin.startsWith("Env/Cloud/App:") || origin.startsWith("Params/App:")) {
            return name != null ? "# application: " + name : "# application";
        }
        if (lower.contains("sbom")) {
            return lower.contains("resource-profile-baseline") && name != null ? 
                "# sbom, resource-profile-baseline: " + name : "# sbom, resource-profile-baseline";
        }
        if (lower.contains("resource-profile-override")) {
            return name != null ? "# resource-profile-override: " + name : "# resource-profile-override";
        }
        if (lower.contains("calculated") || lower.contains("envgene calculated")) {
            return "# envgene calculated";
        }
        if (lower.contains("pipeline parameter") || lower.contains("extra_params") || lower.contains("extra-params")) {
            return "# envgene pipeline parameter";
        }
        if (lower.contains("envgene default") || lower.equals("default")) {
            return "# envgene default";
        }
        return origin.length() > 100 ? "# " + origin.substring(0, 97) + "..." : "# " + origin;
    }
    
    private String extractNameAfterColon(String origin) {
        return extractNameAfterColon(origin, ":", 0);
    }
    
    private String extractNameAfterColon(String origin, String delimiter, int index) {
        int colonIdx = origin.indexOf(":");
        if (colonIdx < 0) return null;
        String afterColon = origin.substring(colonIdx + 1).trim();
        if (afterColon.isEmpty()) return null;
        String[] parts = afterColon.split(delimiter);
        if (index < parts.length && !parts[index].trim().isEmpty()) {
            return parts[index].trim();
        }
        return parts.length > 0 && !parts[parts.length - 1].trim().isEmpty() ? parts[parts.length - 1].trim() : null;
    }
    
    private String addInlineComments(String yamlContent, Map<String, String> originMap) {
        if (originMap.isEmpty()) return yamlContent;
        
        Map<String, String> keyToComment = new TreeMap<>();
        for (Map.Entry<String, String> entry : originMap.entrySet()) {
            String comment = convertOriginToComment(entry.getValue());
            keyToComment.put(entry.getKey(), comment);
            int lastDot = entry.getKey().lastIndexOf('.');
            if (lastDot >= 0) {
                keyToComment.putIfAbsent(entry.getKey().substring(lastDot + 1), comment);
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
            
            if (pendingComments.containsKey(i)) {
                line = appendComment(line, pendingComments.remove(i));
            }
            
            if (trimmedLine.isEmpty() || trimmedLine.startsWith("#") || 
                trimmedLine.startsWith("&") || trimmedLine.startsWith("*") || trimmedLine.startsWith("<<")) {
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
                
                String currentPath = pathStack.isEmpty() ? keyName : String.join(".", pathStack) + "." + keyName;
                String comment = keyToComment.getOrDefault(currentPath, keyToComment.get(keyName));
                
                if (comment != null && !comment.isEmpty()) {
                    String valuePart = trimmedLine.substring(trimmedLine.indexOf(':') + 1).trim();
                    boolean isMultiline = valuePart.matches("[|>][-+]?");
                    
                    if (isMultiline) {
                        result.append(line.substring(0, indent)).append(comment).append("\n").append(line).append("\n");
                    } else {
                        int colonIndex = line.indexOf(':');
                        String afterColon = line.substring(colonIndex + 1);
                        
                        if (afterColon.trim().isEmpty()) {
                            int nextLineIndex = findNextValueLine(lines, i + 1);
                            if (nextLineIndex > 0) pendingComments.put(nextLineIndex, comment);
                            result.append(line).append("\n");
                        } else {
                            result.append(line.substring(0, colonIndex + 1)).append(appendComment(afterColon, comment)).append("\n");
                        }
                    }
                } else {
                    result.append(line).append("\n");
                }
                
                String valuePart = trimmedLine.substring(trimmedLine.indexOf(':') + 1).trim();
                if (valuePart.isEmpty() || valuePart.matches("[|>][-+]?")) {
                    pathStack.add(keyName);
                    indentStack.add(indent);
                }
            } else {
                result.append(line).append("\n");
            }
        }
        
        return result.toString();
    }
    
    private String appendComment(String line, String comment) {
        int valueEndIndex = line.contains("#") ? line.indexOf("#") : line.length();
        while (valueEndIndex > 0 && line.charAt(valueEndIndex - 1) == ' ') valueEndIndex--;
        return line.substring(0, valueEndIndex) + " " + comment;
    }
    
    private int findNextValueLine(String[] lines, int start) {
        for (int i = start; i < lines.length; i++) {
            String trimmed = lines[i].trim();
            if (!trimmed.isEmpty() && !trimmed.startsWith("#") && 
                !trimmed.startsWith("&") && !trimmed.startsWith("*") && !trimmed.startsWith("<<")) {
                return i;
            }
        }
        return -1;
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
