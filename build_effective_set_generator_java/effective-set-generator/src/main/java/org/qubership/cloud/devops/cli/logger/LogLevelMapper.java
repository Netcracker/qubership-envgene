package org.qubership.cloud.devops.cli.logger;

import jakarta.enterprise.context.ApplicationScoped;
import org.eclipse.microprofile.config.inject.ConfigProperty;
import org.jboss.logging.Logger.Level;

@ApplicationScoped
public class LogLevelMapper {

    @ConfigProperty(name = "ENVGENE_LOG_LEVEL", defaultValue = "INFO")
    String level;

    public Level getMappedLevel() {
        return switch (level.toUpperCase()) {
            case "CRITICAL" -> Level.FATAL;
            case "ERROR" -> Level.ERROR;
            case "WARNING" -> Level.WARN;
            case "INFO" -> Level.INFO;
            case "DEBUG" -> Level.DEBUG;
            case "TRACE" -> Level.TRACE;
            default -> Level.INFO;
        };
    }
}
