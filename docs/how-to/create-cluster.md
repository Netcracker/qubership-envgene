# Cluster Creation Guide

## Description

This guide explains the process of creating a new cluster in the Instance Repository.

## Prerequisites

1. **Instance Repository**
   - Ensure that the Instance repository has been created with following folder structure:

    ```text
    ├── configuration
    │   ├── credentials
    │   │   ├── credentials.yml
    │   ├── config.yml
    │   ├── deployer.yml
    │   ├── registry.yml
    ├── environments
    ```

## Flow

1. **Clone (pull updates) the remote Instance repository to the local machine.**

2. **Create a Cluster folder inside `/environments`**.
  
   There are two ways to create the folder:
    - Copy an existing cluster folder, rename it, and remove unused files.
    - Create the cluster folder manually.

   **Sample structure:**

   ```plaintext
   |_ environments
      |_ example-cloud
   ```
