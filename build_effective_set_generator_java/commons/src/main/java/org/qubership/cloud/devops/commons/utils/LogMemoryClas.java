package org.qubership.cloud.devops.commons.utils;

import com.sun.management.OperatingSystemMXBean;

import java.lang.management.BufferPoolMXBean;
import java.lang.management.ManagementFactory;
import java.lang.management.MemoryMXBean;
import java.lang.management.MemoryUsage;

import static org.qubership.cloud.devops.commons.utils.ConsoleLogger.logInfo;

public class LogMemoryClas {

    private static final boolean enabled = true;


    public static void logMemoryUsage(String phase) {
        if (enabled) {

            MemoryMXBean memoryMXBean = ManagementFactory.getMemoryMXBean();
            MemoryUsage heap = memoryMXBean.getHeapMemoryUsage();
            MemoryUsage nonHeap = memoryMXBean.getNonHeapMemoryUsage();

            long heapUsed = heap.getUsed();
            long nonHeapUsed = nonHeap.getUsed();

            long directMemory = getDirectMemory();

            // CPU
            OperatingSystemMXBean osBean =
                    (OperatingSystemMXBean) ManagementFactory.getOperatingSystemMXBean();

            double processCpu =
                    osBean.getProcessCpuLoad() >= 0
                            ? osBean.getProcessCpuLoad() * 100
                            : -1;

            int cores = osBean.getAvailableProcessors();
            logInfo(String.format(
                    "[STATS] %s | Heap=%dMB NonHeap=%dMB Direct=%dMB Total=%dMB | CPU=%.2f%% | Cores=%d",
                    phase,
                    toMB(heapUsed),
                    toMB(nonHeapUsed),
                    toMB(directMemory),
                    toMB(heapUsed + nonHeapUsed + directMemory),
                    processCpu,
                    cores
            ));
        }
    }

    private static long getDirectMemory() {
        for (BufferPoolMXBean pool :
                ManagementFactory.getPlatformMXBeans(BufferPoolMXBean.class)) {
            if ("direct".equalsIgnoreCase(pool.getName())) {
                return pool.getMemoryUsed();
            }
        }
        return 0;
    }

    private static long toMB(long bytes) {
        return bytes / (1024 * 1024);
    }
}
