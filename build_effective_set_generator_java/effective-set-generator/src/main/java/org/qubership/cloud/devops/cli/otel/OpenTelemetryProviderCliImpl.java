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

package org.qubership.cloud.devops.cli.otel;

import org.qubership.cloud.devops.commons.utils.otel.OpenTelemetryProvider;
import edu.umd.cs.findbugs.annotations.NonNull;
import io.opentelemetry.api.trace.NoopTracer;
import io.opentelemetry.api.trace.Tracer;
import io.quarkus.arc.Unremovable;
import jakarta.enterprise.context.ApplicationScoped;

@ApplicationScoped
@Unremovable
public class OpenTelemetryProviderCliImpl implements OpenTelemetryProvider {
    @NonNull
    @Override
    public Tracer getTracer() {
        return new NoopTracer();
    }

    @Override
    public <T, E extends Exception> T withSpan(String spanName, ThrowingSupplier<T, E> delegate) throws E {
        return delegate.get();
    }
}
