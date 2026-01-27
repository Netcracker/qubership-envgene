package org.qubership.cloud.devops.cli.pojo.dto.shared;

import lombok.Getter;

@Getter
public enum EffectiveSetVersion {
    V1_0("v1.0"),
    V2_0("v2.0");

    private final String value;

    EffectiveSetVersion(String value) {
        this.value = value;
    }

    public static EffectiveSetVersion fromString(String value) {
        for (EffectiveSetVersion version : values()) {
            if (version.value.equalsIgnoreCase(value)) {
                return version;
            }
        }
        throw new IllegalArgumentException("Invalid version of effective set: " + value);
    }
}

