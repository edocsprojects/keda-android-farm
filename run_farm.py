import subprocess
import time
import sys
import os

# --- Configuration ---
KEDA_LOCAL_FILE = "keda-2.10.1.yaml"
IMAGE_NAME = "android-farm:latest"
CLUSTER_NAME = "android-cluster"

# --- Commands ---
PRE_CLEANUP_COMMAND = ["k3d", "cluster", "delete", CLUSTER_NAME]
BUILD_COMMAND = ["docker", "build", "-t", IMAGE_NAME, "."]
CREATE_CLUSTER_COMMAND = ["k3d", "cluster", "create", CLUSTER_NAME]
IMPORT_IMAGE_COMMAND = ["k3d", "image", "import", IMAGE_NAME, "-c", CLUSTER_NAME]
APPLY_KEDA_COMMAND = ["kubectl", "apply", "-f", KEDA_LOCAL_FILE]
APPLY_DEMO_COMMAND = ["kubectl", "apply", "-f", "keda-farm.yaml"]
WAIT_COMMAND = ["kubectl", "wait", "--for=condition=ready", "pod", "-l", "app=redis", "-n", "keda", "--timeout=120s"]
PORT_FORWARD_COMMAND = ["kubectl", "port-forward", "svc/redis-service", "-n", "keda", "6379:6379"]
CLEANUP_COMMAND = ["k3d", "cluster", "delete", CLUSTER_NAME]

# --- Functions ---
def run_command(command, step_name):
    """Executes a shell command, prints its status, and handles errors."""
    print(f"\n> {step_name}...")
    try:
        subprocess.run(command, check=True, text=True, stdout=sys.stdout, stderr=sys.stderr)
        print(f"> {step_name}: Success.")
    except subprocess.CalledProcessError as e:
        print(f"Error on step '{step_name}': Command failed.")
        sys.exit(1)
    except FileNotFoundError:
        print(f"Error: Command not found: '{command[0]}'. Is it installed and in your PATH?")
        sys.exit(1)


def main():
    """Sets up and manages the test farm environment."""
    port_forward_process = None
    try:
        print("\nPerforming pre-flight cleanup...")
        try:
            subprocess.run(PRE_CLEANUP_COMMAND, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("Old cluster found and removed.")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("No old cluster found. Starting fresh.")
            pass
        
        run_command(BUILD_COMMAND, "1: Build Image")
        run_command(CREATE_CLUSTER_COMMAND, "2: Create Cluster")
        run_command(IMPORT_IMAGE_COMMAND, "3: Import Image")
        run_command(APPLY_KEDA_COMMAND, "4: Apply KEDA")
        run_command(APPLY_DEMO_COMMAND, "5: Apply Demo App")
        run_command(WAIT_COMMAND, "6: Wait for Redis Pod")
        
        print("\n> Step 7: Starting Redis port-forward...")
        port_forward_process = subprocess.Popen(PORT_FORWARD_COMMAND, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(3)
        if port_forward_process.poll() is not None:
            print("Error: Port-forward command failed to start.")
            sys.exit(1)
        print("> Step 7: Starting Redis port-forward: Success.")

        print("\nSetup Complete.")
        print("\nOpen other terminals to run:")
        print("1. 'kubectl get pods -n keda -w' (to monitor the farm)")
        print("2. 'python3 run_test.py' (to create jobs)")
        print("3. 'python3 run_viewer.py' (to watch an emulator)")
        print("\nPress CTRL+C in this window to shut down the farm.")

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n\nShutdown signal received.")
    finally:
        print("\nCleaning up resources...")
        if port_forward_process:
            port_forward_process.terminate()
        run_command(CLEANUP_COMMAND, "Cleanup")
        print("Cleanup complete.")

# --- Main ---
if __name__ == "__main__":
    main()