package org.qubership.cloud.devops.cli.utils.deserializer;

import com.fasterxml.jackson.databind.annotation.JsonDeserialize;

import java.util.Date;

public abstract class BomMixin {

    @JsonDeserialize(using = CustomMetadataDeserializer.class)
    abstract Date getMetadata();
}
