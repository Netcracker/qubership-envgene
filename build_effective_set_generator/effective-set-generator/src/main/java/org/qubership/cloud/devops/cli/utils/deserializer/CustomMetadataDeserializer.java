package org.qubership.cloud.devops.cli.utils.deserializer;

import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.databind.DeserializationContext;
import com.fasterxml.jackson.databind.JsonDeserializer;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.cyclonedx.model.*;
import org.cyclonedx.util.ToolsJsonParser;
import org.cyclonedx.util.deserializer.LicenseDeserializer;
import org.cyclonedx.util.deserializer.LifecycleDeserializer;
import org.cyclonedx.util.deserializer.PropertiesDeserializer;

import java.io.IOException;
import java.time.ZonedDateTime;
import java.util.ArrayList;
import java.util.Date;
import java.util.Iterator;
import java.util.List;

public class CustomMetadataDeserializer extends JsonDeserializer<Metadata> {

    private final LifecycleDeserializer lifecycleDeserializer = new LifecycleDeserializer();
    private final PropertiesDeserializer propertiesDeserializer = new PropertiesDeserializer();
    private final LicenseDeserializer licenseDeserializer = new LicenseDeserializer();

    public CustomMetadataDeserializer() {
    }

    public Metadata deserialize(JsonParser jsonParser, DeserializationContext ctxt) throws IOException {
        JsonNode node = (JsonNode) jsonParser.getCodec().readTree(jsonParser);
        Metadata metadata = new Metadata();
        ObjectMapper mapper = this.getMapper(jsonParser);
        List properties;
        if (node.has("authors")) {
            JsonNode authorsNode = node.get("authors");
            properties = deserializeOrganizationalContact(authorsNode, mapper);
            metadata.setAuthors(properties);
        }

        if (node.has("component")) {
            Component component = (Component) mapper.convertValue(node.get("component"), Component.class);
            metadata.setComponent(component);
        }

        OrganizationalEntity supplier;
        if (node.has("manufacture")) {
            supplier = (OrganizationalEntity) mapper.convertValue(node.get("manufacture"), OrganizationalEntity.class);
            metadata.setManufacture(supplier);
        }

        if (node.has("manufacturer")) {
            supplier = (OrganizationalEntity) mapper.convertValue(node.get("manufacturer"), OrganizationalEntity.class);
            metadata.setManufacturer(supplier);
        }

        JsonParser propertiesParser;
        if (node.has("lifecycles")) {
            propertiesParser = node.get("lifecycles").traverse(jsonParser.getCodec());
            propertiesParser.nextToken();
            Lifecycles lifecycles = this.lifecycleDeserializer.deserialize(propertiesParser, ctxt);
            metadata.setLifecycles(lifecycles);
        }

        if (node.has("supplier")) {
            supplier = (OrganizationalEntity) mapper.convertValue(node.get("supplier"), OrganizationalEntity.class);
            metadata.setSupplier(supplier);
        }

        if (node.has("licenses")) {
            propertiesParser = node.get("licenses").traverse(jsonParser.getCodec());
            propertiesParser.nextToken();
            LicenseChoice licenses = this.licenseDeserializer.deserialize(propertiesParser, ctxt);
            metadata.setLicenses(licenses);
        }

        if (node.has("timestamp")) {
            this.setTimestamp(node, metadata);
        }

        if (node.has("properties")) {
            propertiesParser = node.get("properties").traverse(jsonParser.getCodec());
            propertiesParser.nextToken();
            properties = this.propertiesDeserializer.deserialize(propertiesParser, ctxt);
            metadata.setProperties(properties);
        }

        if (node.has("tools")) {
            ToolsJsonParser toolsParser = new ToolsJsonParser(node, jsonParser, ctxt);
            metadata.setTools(toolsParser.getTools());
            metadata.setToolChoice(toolsParser.getToolInformation());
        }

        return metadata;
    }

    static List<OrganizationalContact> deserializeOrganizationalContact(JsonNode node, ObjectMapper mapper) {
        List<OrganizationalContact> organizationalContactList = new ArrayList();
        if (node.has("author")) {
            node = node.get("author");
        }

        if (node.isArray()) {
            Iterator var3 = node.iterator();

            while (var3.hasNext()) {
                JsonNode authorNode = (JsonNode) var3.next();
                deserializeAuthor(authorNode, mapper, organizationalContactList);
            }
        } else if (node.isObject()) {
            deserializeAuthor(node, mapper, organizationalContactList);
        }

        return organizationalContactList;
    }

    static void deserializeAuthor(JsonNode node, ObjectMapper mapper, List<OrganizationalContact> organizationalContactList) {
        OrganizationalContact author = (OrganizationalContact) mapper.convertValue(node, OrganizationalContact.class);
        organizationalContactList.add(author);
    }

    private ObjectMapper getMapper(JsonParser jsonParser) {
        return jsonParser.getCodec() instanceof ObjectMapper ? (ObjectMapper) jsonParser.getCodec() : new ObjectMapper();
    }

    private void setTimestamp(JsonNode node, Metadata metadata) {
        //custom timestamp setting
        JsonNode timestampNode = node.get("timestamp");
        try {
            ZonedDateTime date = ZonedDateTime.parse(timestampNode.asText());
            metadata.setTimestamp(Date.from(date.toInstant()));
        } catch (Exception e) {
            metadata.setTimestamp(null);
            System.out.println("Error dezerializing date");
        }


    }
}
