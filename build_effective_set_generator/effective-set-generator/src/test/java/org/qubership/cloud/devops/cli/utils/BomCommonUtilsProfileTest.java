package org.qubership.cloud.devops.cli.utils;

import com.fasterxml.jackson.core.type.TypeReference;
import org.cyclonedx.model.AttachmentText;
import org.cyclonedx.model.Component;
import org.cyclonedx.model.component.data.ComponentData;
import org.cyclonedx.model.component.data.Content;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.qubership.cloud.devops.cli.service.implementation.ProfileServiceCliImpl;
import org.qubership.cloud.devops.commons.pojo.profile.model.ApplicationProfile;
import org.qubership.cloud.devops.commons.pojo.profile.model.ParameterProfile;
import org.qubership.cloud.devops.commons.pojo.profile.model.Profile;
import org.qubership.cloud.devops.commons.pojo.profile.model.ServiceProfile;
import org.qubership.cloud.devops.commons.repository.interfaces.FileDataConverter;
import org.qubership.cloud.devops.commons.utils.ConsoleLogger;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.logging.Handler;
import java.util.logging.Level;
import java.util.logging.LogRecord;
import java.util.logging.Logger;

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
    private final List<String> warnings = new ArrayList<>();
    private final Logger consoleLogger = Logger.getLogger(ConsoleLogger.class.getName());
    private final Handler warningCollector = new Handler() {
        @Override
        public void publish(LogRecord logRecord) {
            if (logRecord.getLevel().intValue() == Level.WARNING.intValue()) {
                warnings.add(logRecord.getMessage());
            }
        }

        @Override
        public void flush() {
        }

        @Override
        public void close() {
        }
    };

    @BeforeEach
    @SuppressWarnings("unchecked")
    void setUp() {
        FileDataConverter converter = mock(FileDataConverter.class);
        when(converter.decodeAndParse(eq("dev"), any(TypeReference.class)))
                .thenAnswer(i -> new HashMap<>(Map.of("replicas", 1, "cpu", "100m")));
        when(converter.decodeAndParse(eq("prod"), any(TypeReference.class)))
                .thenAnswer(i -> new HashMap<>(Map.of("replicas", 2, "cpu", "1")));
        when(converter.decodeAndParse(eq("nested"), any(TypeReference.class)))
                .thenAnswer(i -> new HashMap<>(Map.of("resources.cpu", "1")));
        bomCommonUtils = new BomCommonUtils(converter, null, new ProfileServiceCliImpl(null, null, null));
        consoleLogger.addHandler(warningCollector);
    }

    @AfterEach
    void tearDown() {
        consoleLogger.removeHandler(warningCollector);
    }

    private static Component baselines(String... names) {
        return baselineFiles(Arrays.stream(names).map(name -> baselineFile(name + ".yaml", name)).toList());
    }

    private static Component baselineFiles(List<ComponentData> files) {
        Component component = new Component();
        component.setData(files);
        return component;
    }

    private static ComponentData baselineFile(String fileName, String contentKey) {
        AttachmentText text = new AttachmentText();
        text.setText(contentKey);
        Content content = new Content();
        content.setAttachment(text);
        ComponentData data = new ComponentData();
        data.setName(fileName);
        data.setContents(content);
        return data;
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

    @Test
    void overrideForOtherApplicationIsIgnored() {
        ServiceProfile serviceProfile = ServiceProfile.builder().name(SERVICE)
                .parameters(List.of(ParameterProfile.builder().name("replicas").value(3).build())).build();
        Profile otherApp = Profile.builder().name("over")
                .applications(List.of(ApplicationProfile.builder().name("crm").services(List.of(serviceProfile)).build()))
                .build();
        assertEquals(Map.of("replicas", 2, "cpu", "1"), resolve(baselines("dev", "prod"), "prod", otherApp));
    }

    @Test
    void overrideServiceWithEmptyParametersAppliesNothing() {
        ServiceProfile serviceProfile = ServiceProfile.builder().name(SERVICE).parameters(List.of()).build();
        Profile emptyService = Profile.builder().name("over")
                .applications(List.of(ApplicationProfile.builder().name(APP).services(List.of(serviceProfile)).build()))
                .build();
        assertTrue(resolve(baselines("dev", "prod"), null, emptyService).isEmpty());
        assertTrue(warnings.isEmpty(), warnings.toString());
    }

    @Test
    void baselineFileNameMatchedByPartBeforeFirstDot() {
        Component files = baselineFiles(List.of(baselineFile("dev.v2.yaml", "dev"), baselineFile("prod.yaml", "prod")));
        assertEquals(Map.of("replicas", 1, "cpu", "100m"), resolve(files, "dev", null));
    }

    @Test
    void dottedKeysAreExpandedIntoNestedValues() {
        Map<String, Object> values = resolve(baselines("nested"), "nested", override(SERVICE, "resources.memory", "2Gi"));
        assertEquals(Map.of("resources", Map.of("cpu", "1", "memory", "2Gi")), values);
    }

    @Test
    void unmatchedBaselineWithoutOverrideWarns() {
        resolve(baselines("dev", "prod"), "large", null);
        assertEquals(1, warnings.size(), warnings.toString());
    }

    @Test
    void sameWarningIsReportedOnce() {
        resolve(baselines("dev", "prod"), "large", override(SERVICE, "replicas", 3));
        resolve(baselines("dev", "prod"), "large", override(SERVICE, "replicas", 3));
        assertEquals(1, warnings.size(), warnings.toString());
    }

    @Test
    void unmatchedBaselineWarns() {
        resolve(baselines("dev", "prod"), "large", override(SERVICE, "replicas", 3));
        assertEquals(1, warnings.size(), warnings.toString());
    }

    @Test
    void serviceWithoutBaselinesIsNotWarned() {
        resolve(null, "prod", override(SERVICE, "replicas", 3));
        assertTrue(warnings.isEmpty(), warnings.toString());
    }

    @Test
    void appliedOverrideWithoutBaselineWarns() {
        resolve(baselines("dev", "prod"), null, override(SERVICE, "replicas", 3));
        assertEquals(1, warnings.size(), warnings.toString());
    }

    @Test
    void overrideForOtherServiceWithoutBaselineIsNotWarned() {
        resolve(baselines("dev", "prod"), null, override("billing-ui", "replicas", 3));
        assertTrue(warnings.isEmpty(), warnings.toString());
    }

    @Test
    void matchedBaselineWithOverrideIsNotWarned() {
        resolve(baselines("dev", "prod"), "prod", override(SERVICE, "replicas", 3));
        assertTrue(warnings.isEmpty(), warnings.toString());
    }
}
