FROM registry.access.redhat.com/ubi8/ubi-minimal:8.1 AS builder

ARG JAVA_PACKAGE=java-17-openjdk-headless
ARG JAVA_PACKAGE_VERSION=1:17.0.13.0.11-2.el8_10
ARG RUN_JAVA_VERSION=1.3.8

RUN microdnf install -y \
        curl-7.61.1-33.el8 \
        ca-certificates-2023.2.60_v7.0.306-91.el8_10 \
        ${JAVA_PACKAGE}-${JAVA_PACKAGE_VERSION} && \
    microdnf clean all && \
    mkdir -p /deployments && \
    curl -s https://repo1.maven.org/maven2/io/fabric8/run-java-sh/${RUN_JAVA_VERSION}/run-java-sh-${RUN_JAVA_VERSION}-sh.sh -o /deployments/run-java.sh && \
    chmod 540 /deployments/run-java.sh && \
    echo "securerandom.source=file:/dev/urandom" >> /etc/alternatives/jre/lib/security/java.security

COPY downloaded_artifact/build_effective_set_generator_java/effective-set-generator/target/*.jar /deployments/app.jar

FROM registry.access.redhat.com/ubi8/ubi-minimal:8.1

ENV LANG='en_US.UTF-8' LANGUAGE='en_US:en'

COPY --from=builder --chown=1001:root /deployments /deployments
COPY --from=builder /etc/alternatives/jre/lib/security/java.security /etc/alternatives/jre/lib/security/java.security

RUN chmod g+rwX /deployments

# Ensure sane permissions on copied tree without findutils
RUN chmod -R u=rwX,go=rX /deployments && \
    chmod 540 /deployments/run-java.sh

USER 1001

ENTRYPOINT [ "/deployments/run-java.sh" ]
