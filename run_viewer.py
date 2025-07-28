import subprocess
import webbrowser
import time
import sys

# --- Functions ---
def get_emulator_pods():
    """Returns a list of running android-emulator pods in the keda namespace."""
    command = [
        "kubectl", "get", "pods",
        "-n", "keda",
        "-l", "app=android-emulator",
        "-o", "jsonpath={.items[*].metadata.name}"
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        pods = result.stdout.strip().split()
        return pods
    except subprocess.CalledProcessError:
        print("Error: Could not list pods. Is kubectl connected to the right cluster?")
        return []
    except FileNotFoundError:
        print("Error: 'kubectl' command not found. Is it installed and in your PATH?")
        return []

def main():
    """Finds running emulators, prompts the user for a selection, and opens a VNC viewer."""
    print("\n> 1: Finding running emulator pods...")
    running_pods = get_emulator_pods()

    if not running_pods:
        print("> 1: Finding running emulator pods: Failed. No pods found.")
        sys.exit(0)
    print(f"> 1: Finding running emulator pods: Success. Found {len(running_pods)} pod(s).")

    print("\nPlease select a pod to watch:")
    for i, pod_name in enumerate(running_pods):
        print(f"  [{i}] {pod_name}")

    choice = -1
    while True:
        try:
            raw_choice = input(f"\nEnter pod number [0-{len(running_pods)-1}]: ")
            choice = int(raw_choice)
            if 0 <= choice < len(running_pods):
                break
            else:
                print(f"Invalid selection. Please enter a number between 0 and {len(running_pods)-1}.")
        except ValueError:
            print("Invalid input. Please enter a number.")
    
    selected_pod = running_pods[choice]
    local_port = 6081 + choice 
    
    port_forward_command = [
        "kubectl", "port-forward",
        "-n", "keda",
        selected_pod, f"{local_port}:6080"
    ]
    
    view_url = f"http://localhost:{local_port}"
    port_forward_process = None

    try:
        print(f"\n> 2: Starting VNC viewer for '{selected_pod}'...")
        port_forward_process = subprocess.Popen(port_forward_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)
        
        webbrowser.open_new_tab(view_url)
        print(f"> 2: Starting VNC viewer: Success. Opening {view_url}")
        
        print("\nPort-forward is active. Press CTRL+C to stop.")
        
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n\nShutdown signal received.")
    finally:
        print("\nCleaning up resources...")
        if port_forward_process:
            port_forward_process.terminate()
        print("Cleanup complete.")

# --- Main ---
if __name__ == "__main__":
    main()
