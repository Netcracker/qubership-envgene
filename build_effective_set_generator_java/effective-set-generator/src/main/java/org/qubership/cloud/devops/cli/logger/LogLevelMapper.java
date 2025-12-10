package org.qubership.cloud.devops.cli.logger;

import jakarta.enterprise.context.ApplicationScoped;
import org.eclipse.microprofile.config.inject.ConfigProperty;
import org.jboss.logging.Logger.Level;

@ApplicationScoped
public class LogLevelMapper {

    @ConfigProperty(name = "LOG_LEVEL", defaultValue = "INFO")
    String level;

    public Level getMappedLevel() {
        switch (level.toUpperCase()) {
            case "CRITICAL":
                return Level.FATAL;
            case "ERROR":
                return Level.ERROR;
            case "WARNING":
                return Level.WARN;
            case "INFO":
                return Level.INFO;
            case "DEBUG":
                return Level.DEBUG;
            case "TRACE":
                return Level.TRACE;
            default:
                return Level.INFO;
        }
    }
}
