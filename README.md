# Android Emulator Farm on Kubernetes

This project demonstrates a scalable Android emulator farm running on a local Kubernetes (k3d) cluster. It uses **KEDA** to automatically scale the number of running emulator pods based on the length of a job queue in Redis.

## Acknowledgements

* This project relies on the excellent **`budtmo/docker-android`** base image, which provides a robust, containerized Android emulator environment.
* The auto-scaling functionality is powered by **KEDA** (Kubernetes-based Event-driven Autoscaling). The `keda-2.10.1.yaml` manifest is from the official KEDA v2.10.1 release.

---
## Prerequisites

Before you begin, ensure you have the following tools installed:
* [Docker](https://www.docker.com/)
* [k3d](https://k3d.io/) (v5.x or later)
* [kubectl](https://kubernetes.io/docs/tasks/tools/)
* [Python 3](https://www.python.org/) and Pip

Confirm that your Python Environment is included in the .dockerignore the default currently is venv and .venv

Adjust the configs of CPU and RAM usage inside keda-farm.yaml

---
## Setup

1.  **Clone the Repository**
    ```bash
    git clone [<your-repo-url>](https://github.com/edocsprojects/keda-android-farm)
    cd <your-repo-directory>
    ```

2.  **Install Python Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Start the Farm**
    Run the main orchestration script. This will automatically build the Docker image, push it to your local registry, create the k3d cluster, and deploy all necessary components.
    ```bash
    python3 run_farm.py
    ```
    Once the setup is complete, you will see instructions for how to interact with the farm.

---
## Usage

With the farm running, you can open new terminal windows to perform the following actions.

#### To Run a Test
This script submits a new job to the Redis queue, which will cause KEDA to scale up a new emulator pod to handle the test.
```bash
python3 run_test.py
