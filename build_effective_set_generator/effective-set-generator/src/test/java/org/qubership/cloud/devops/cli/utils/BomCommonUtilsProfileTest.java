package org.qubership.cloud.devops.cli.utils;

import com.fasterxml.jackson.core.type.TypeReference;
import org.cyclonedx.model.AttachmentText;
import org.cyclonedx.model.Component;
import org.cyclonedx.model.component.data.ComponentData;
import org.cyclonedx.model.component.data.Content;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.qubership.cloud.devops.cli.service.implementation.ProfileServiceCliImpl;
import org.qubership.cloud.devops.commons.pojo.profile.model.ApplicationProfile;
import org.qubership.cloud.devops.commons.pojo.profile.model.ParameterProfile;
import org.qubership.cloud.devops.commons.pojo.profile.model.Profile;
import org.qubership.cloud.devops.commons.pojo.profile.model.ServiceProfile;
import org.qubership.cloud.devops.commons.repository.interfaces.FileDataConverter;

import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

class BomCommonUtilsProfileTest {

    private static final String APP = "billing";
    private static final String SERVICE = "billing-api";

    private BomCommonUtils bomCommonUtils;

    @BeforeEach
    @SuppressWarnings("unchecked")
    void setUp() {
        FileDataConverter converter = mock(FileDataConverter.class);
        when(converter.decodeAndParse(eq("dev"), any(TypeReference.class)))
                .thenAnswer(i -> new HashMap<>(Map.of("replicas", 1, "cpu", "100m")));
        when(converter.decodeAndParse(eq("prod"), any(TypeReference.class)))
                .thenAnswer(i -> new HashMap<>(Map.of("replicas", 2, "cpu", "1")));
        bomCommonUtils = new BomCommonUtils(converter, null, new ProfileServiceCliImpl(null, null, null));
    }

    private static Component baselines(String... names) {
        Component component = new Component();
        component.setData(Arrays.stream(names).map(name -> {
            AttachmentText text = new AttachmentText();
            text.setText(name);
            Content content = new Content();
            content.setAttachment(text);
            ComponentData data = new ComponentData();
            data.setName(name + ".yaml");
            data.setContents(content);
            return data;
        }).toList());
        return component;
    }

    private static Profile override(String service, String param, Object value) {
        ServiceProfile serviceProfile = ServiceProfile.builder().name(service)
                .parameters(List.of(ParameterProfile.builder().name(param).value(value).build())).build();
        return Profile.builder().name("over")
                .applications(List.of(ApplicationProfile.builder().name(APP).services(List.of(serviceProfile)).build()))
                .build();
    }

    private Map<String, Object> resolve(Component serviceBaselines, String baseline, Profile override) {
        Map<String, Object> values = new HashMap<>();
        bomCommonUtils.fillProfileValues(values, serviceBaselines, APP, SERVICE, override, baseline);
        return values;
    }

    @Test
    void matchedBaselineWithoutOverride() {
        assertEquals(Map.of("replicas", 1, "cpu", "100m"), resolve(baselines("dev", "prod"), "dev", null));
    }

    @Test
    void matchedBaselinePlusOverride() {
        assertEquals(Map.of("replicas", 3, "cpu", "1"),
                resolve(baselines("dev", "prod"), "prod", override(SERVICE, "replicas", 3)));
    }

    @Test
    void unmatchedBaselineWithoutOverrideGivesNothing() {
        assertTrue(resolve(baselines("dev", "prod"), "large", null).isEmpty());
    }

    @Test
    void unmatchedBaselineStillAppliesOverride() {
        assertEquals(Map.of("replicas", 3),
                resolve(baselines("dev", "prod"), "large", override(SERVICE, "replicas", 3)));
    }

    @Test
    void serviceWithoutBaselinesGetsOverride() {
        assertEquals(Map.of("replicas", 3), resolve(null, "prod", override(SERVICE, "replicas", 3)));
    }

    @Test
    void serviceWithoutBaselinesAndOverrideGetsNothing() {
        assertTrue(resolve(null, "prod", null).isEmpty());
    }

    @Test
    void noBaselineAppliesOverrideOnly() {
        assertEquals(Map.of("replicas", 3),
                resolve(baselines("dev", "prod"), null, override(SERVICE, "replicas", 3)));
    }

    @Test
    void noBaselineNoOverrideGivesNothing() {
        assertTrue(resolve(baselines("dev", "prod"), null, null).isEmpty());
    }

    @Test
    void overrideForOtherServiceIsIgnored() {
        assertEquals(Map.of("replicas", 2, "cpu", "1"),
                resolve(baselines("dev", "prod"), "prod", override("billing-ui", "replicas", 3)));
    }

    @Test
    void baselineOnlyOverrideWithoutApplications() {
        Profile baselineOnly = Profile.builder().name("over").baseline("prod").build();
        assertEquals(Map.of("replicas", 2, "cpu", "1"), resolve(baselines("dev", "prod"), "prod", baselineOnly));
    }
}
