package org.qubership.cloud.parameters.processor.expression.binding;

import org.junit.jupiter.api.Test;
import org.qubership.cloud.devops.commons.pojo.clouds.model.Cloud;
import org.qubership.cloud.devops.commons.pojo.namespaces.model.Namespace;
import org.qubership.cloud.devops.commons.pojo.profile.model.Profile;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertSame;

class ProfileSelectionTest {

    private static final Profile CLOUD_OVERRIDE = Profile.builder().name("cloud-over").baseline("prod").build();

    private static Namespace namespace(String baseline, Profile override) {
        Cloud cloud = Cloud.builder().baseline("cloud-baseline").profile(CLOUD_OVERRIDE).build();
        return Namespace.builder().baseline(baseline).profile(override).cloud(cloud).build();
    }

    private static Profile override(String baseline) {
        return Profile.builder().name("ns-over").baseline(baseline).build();
    }

    @Test
    void objectBaselineWithoutOverride() {
        ProfileSelection selection = ProfileSelection.of(namespace("dev", null));
        assertEquals("dev", selection.baseline());
        assertNull(selection.override());
    }

    @Test
    void overrideBaselineWinsOverObjectBaseline() {
        assertEquals("prod", ProfileSelection.of(namespace("dev", override("prod"))).baseline());
    }

    @Test
    void overrideBaselineWithoutObjectBaseline() {
        assertEquals("prod", ProfileSelection.of(namespace(null, override("prod"))).baseline());
    }

    @Test
    void objectBaselineWhenOverrideHasNoBaseline() {
        assertEquals("dev", ProfileSelection.of(namespace("dev", override(null))).baseline());
    }

    @Test
    void emptyOverrideBaselineIsAbsent() {
        assertEquals("dev", ProfileSelection.of(namespace("dev", override(""))).baseline());
    }

    @Test
    void emptyObjectBaselineIsAbsent() {
        assertNull(ProfileSelection.of(namespace("", override(null))).baseline());
    }

    @Test
    void namespaceOverrideWithoutBaselineKeepsNamespaceSide() {
        Profile nsOverride = override(null);
        ProfileSelection selection = ProfileSelection.of(namespace(null, nsOverride));
        assertSame(nsOverride, selection.override());
        assertNull(selection.baseline());
    }

    @Test
    void cloudSideWhenNamespaceHasNoSignal() {
        ProfileSelection selection = ProfileSelection.of(namespace("", null));
        assertSame(CLOUD_OVERRIDE, selection.override());
        assertEquals("prod", selection.baseline());
    }

    @Test
    void cloudObjectBaselineWithoutCloudOverride() {
        Cloud cloud = Cloud.builder().baseline("dev").build();
        ProfileSelection selection = ProfileSelection.of(Namespace.builder().cloud(cloud).build());
        assertEquals("dev", selection.baseline());
        assertNull(selection.override());
    }

    @Test
    void noBaselineAnywhere() {
        ProfileSelection selection = ProfileSelection.of(Namespace.builder().cloud(Cloud.builder().build()).build());
        assertNull(selection.baseline());
        assertNull(selection.override());
    }
}
