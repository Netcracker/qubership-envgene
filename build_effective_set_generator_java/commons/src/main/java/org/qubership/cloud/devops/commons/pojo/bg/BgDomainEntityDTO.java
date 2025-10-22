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

    @JsonProperty("originNamespace")
    @JsonIgnoreProperties({"credentialsId", "url", "username", "password"})
    private NamespaceDTO originNamespace;

    @JsonProperty("peerNamespace")
    @JsonIgnoreProperties({"credentialsId", "url", "username", "password"})
    private NamespaceDTO peerNamespace;

    @JsonProperty("controllerNamespace")
    private NamespaceDTO controllerNamespace;

    @Data
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class NamespaceDTO {
        private String name;
        private String type;
        private String credentialsId;
        @JsonProperty("username")
        private String userName;
        private String password;
        private String url;;
    }

}
