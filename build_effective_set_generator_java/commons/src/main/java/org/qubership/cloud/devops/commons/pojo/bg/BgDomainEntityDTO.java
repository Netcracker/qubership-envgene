package org.qubership.cloud.devops.commons.pojo.bg;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonPropertyOrder;
import lombok.Builder;
import lombok.Data;
import lombok.extern.jackson.Jacksonized;

import javax.annotation.Nonnull;


@Data
@Builder
@JsonPropertyOrder
@Jacksonized
@JsonIgnoreProperties(ignoreUnknown = true)
@Nonnull
public class BgDomainEntityDTO {
    private String name;
    private String type;

    @JsonProperty("origin")
    @JsonIgnoreProperties({"credentialsId", "url"})
    private NamespaceDTO origin;

    @JsonProperty("peer")
    @JsonIgnoreProperties({"credentialsId", "url"})
    private NamespaceDTO peer;

    @JsonProperty("controller")
    private NamespaceDTO controller;

    @Data
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class NamespaceDTO {
        private String name;
        private String type;
        private String credentialsId;
        private String url;;
    }

}
