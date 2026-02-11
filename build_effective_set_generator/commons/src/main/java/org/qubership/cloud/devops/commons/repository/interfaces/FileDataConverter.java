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

package org.qubership.cloud.devops.commons.repository.interfaces;

import com.fasterxml.jackson.core.type.TypeReference;
import org.cyclonedx.model.Bom;

import java.io.File;
import java.io.IOException;
import java.util.Map;

public interface FileDataConverter {

    <T> T parseInputFile(Class<T> type, File file);

    Bom parseSbomFile(File file);

    <T> T parseInputFile(TypeReference<T> typeReference, File file);

    <T> T decodeAndParse(String encodedText, TypeReference<T> typeReference);

    <T> T decodeAndParse(String encodedText, Class<T> clazz);

    void writeToFile(Map<String, Object> params, String... args) throws IOException;
    
    void writeToFile(Map<String, Object> params, boolean enableTraceability, String... args) throws IOException;

    <T> Map<String, Object> getObjectMap(T inputObject);
}
