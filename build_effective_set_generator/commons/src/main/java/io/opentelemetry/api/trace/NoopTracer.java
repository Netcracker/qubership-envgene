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

package io.opentelemetry.api.trace;

import io.opentelemetry.api.common.AttributeKey;
import io.opentelemetry.api.common.Attributes;
import io.opentelemetry.api.internal.ApiUsageLogger;
import io.opentelemetry.context.Context;

import javax.annotation.Nullable;
import java.util.concurrent.TimeUnit;

public class NoopTracer implements Tracer {

    @Override
    public SpanBuilder spanBuilder(String s) {
        return NoopSpanBuilder.create();
    }

    private static final class NoopSpanBuilder implements SpanBuilder {
        static NoopSpanBuilder create() {
            return new NoopSpanBuilder();
        }

        @Nullable
        private SpanContext spanContext;

        @Override
        public Span startSpan() {
            if (spanContext == null) {
                spanContext = Span.current().getSpanContext();
            }

            return Span.wrap(spanContext);
        }

        @Override
        public NoopSpanBuilder setParent(Context context) {
            if (context == null) {
                ApiUsageLogger.log("context is null");
                return this;
            }
            spanContext = Span.fromContext(context).getSpanContext();
            return this;
        }

        @Override
        public NoopSpanBuilder setNoParent() {
            spanContext = SpanContext.getInvalid();
            return this;
        }

        @Override
        public NoopSpanBuilder addLink(SpanContext spanContext) {
            return this;
        }

        @Override
        public NoopSpanBuilder addLink(SpanContext spanContext, Attributes attributes) {
            return this;
        }

        @Override
        public NoopSpanBuilder setAttribute(String key, String value) {
            return this;
        }

        @Override
        public NoopSpanBuilder setAttribute(String key, long value) {
            return this;
        }

        @Override
        public NoopSpanBuilder setAttribute(String key, double value) {
            return this;
        }

        @Override
        public NoopSpanBuilder setAttribute(String key, boolean value) {
            return this;
        }

        @Override
        public <T> NoopSpanBuilder setAttribute(AttributeKey<T> key, T value) {
            return this;
        }

        @Override
        public NoopSpanBuilder setAllAttributes(Attributes attributes) {
            return this;
        }

        @Override
        public NoopSpanBuilder setSpanKind(SpanKind spanKind) {
            return this;
        }

        @Override
        public NoopSpanBuilder setStartTimestamp(long startTimestamp, TimeUnit unit) {
            return this;
        }

        private NoopSpanBuilder() {
        }
    }

}
