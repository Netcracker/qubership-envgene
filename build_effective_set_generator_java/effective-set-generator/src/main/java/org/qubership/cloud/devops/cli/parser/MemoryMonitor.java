// package org.qubership.cloud.devops.cli.parser;
// import jakarta.enterprise.context.ApplicationScoped;
// import io.quarkus.scheduler.Scheduled;

// import java.lang.management.*;
// import java.util.List;

// @ApplicationScoped
// public class MemoryMonitor {

//     @Scheduled(every = "1s")
//     void checkMemory() {

//         MemoryMXBean memoryMXBean = ManagementFactory.getMemoryMXBean();
//         MemoryUsage heap = memoryMXBean.getHeapMemoryUsage();
//         MemoryUsage nonHeap = memoryMXBean.getNonHeapMemoryUsage();

//         long heapUsed = heap.getUsed();
//         long nonHeapUsed = nonHeap.getUsed();

//         long directMemory = getDirectMemory();

//         System.out.println("===== JVM Memory =====");
//         System.out.println("Heap Used      : " + toMB(heapUsed) + " MB");
//         System.out.println("Non-Heap Used  : " + toMB(nonHeapUsed) + " MB");
//         System.out.println("Direct Memory  : " + toMB(directMemory) + " MB");
//         System.out.println("Total JVM Used : " +
//                 toMB(heapUsed + nonHeapUsed + directMemory) + " MB");
//     }

//     private long getDirectMemory() {
//         for (BufferPoolMXBean pool :
//                 ManagementFactory.getPlatformMXBeans(BufferPoolMXBean.class)) {
//             if ("direct".equalsIgnoreCase(pool.getName())) {
//                 return pool.getMemoryUsed();
//             }
//         }
//         return 0;
//     }

//     private long toMB(long bytes) {
//         return bytes / (1024 * 1024);
//     }
// }
