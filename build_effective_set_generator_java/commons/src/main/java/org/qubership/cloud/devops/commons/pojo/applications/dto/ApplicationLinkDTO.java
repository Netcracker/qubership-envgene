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

package org.qubership.cloud.devops.commons.pojo.applications.dto;

import com.fasterxml.jackson.annotation.JsonPropertyOrder;
import com.fasterxml.jackson.databind.annotation.JsonDeserialize;
import lombok.Builder;
import lombok.Data;
import lombok.Getter;
import lombok.Setter;
import lombok.extern.jackson.Jacksonized;
import org.qubership.cloud.devops.commons.utils.convert.CustomDeserializer;

import javax.annotation.Nonnull;
import java.util.Map;
import java.util.Objects;


@Nonnull
@JsonPropertyOrder
@Builder
@Jacksonized
@Setter
@Getter
public class ApplicationLinkDTO {
    private final String name;
    @Nonnull
    @JsonDeserialize(using = CustomDeserializer.class)
    private final Map<String, String> deployParameters;
    @JsonDeserialize(using = CustomDeserializer.class)
    private final Map<String, String> technicalConfigurationParameters;

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        ApplicationLinkDTO that = (ApplicationLinkDTO) o;
        return Objects.equals(name, that.name) &&
                Objects.equals(deployParameters, that.deployParameters) &&
                Objects.equals(technicalConfigurationParameters, that.technicalConfigurationParameters);
    }

    @Override
    public int hashCode() {
        return Objects.hash(name, deployParameters, technicalConfigurationParameters);
    }

    @Override
    public String toString() {
        return "ApplicationLinkDTO{" +
                "name='" + name + '\'' +
                ", deployParameters=" + deployParameters +
                ", technicalConfigurationParameters=" + technicalConfigurationParameters +
                '}';
    }
}
