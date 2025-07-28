import time
import redis
import uuid
import sys
import subprocess
import requests
from appium import webdriver
from appium.options.android import UiAutomator2Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

# --- Configuration ---
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
JOB_QUEUE = 'test_queue'
ACTIVE_JOBS_HASH = 'active_jobs'

# --- Functions ---
def get_pod_name_from_ip(pod_ip):
    """Finds a Kubernetes pod's name using its IP address via kubectl."""
    if not pod_ip:
        return None
    command = [
        "kubectl", "get", "pods", "-n", "keda",
        f"--field-selector=status.podIP={pod_ip}",
        "-o", "jsonpath={.items[0].metadata.name}"
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None

def main():
    """Connects to Redis, submits a test job, and runs an Appium test against the resulting emulator."""
    try:
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        r.ping()
        print(f"> Connected to Redis at {REDIS_HOST}: Success.")
    except redis.exceptions.ConnectionError:
        print(f"Error: Could not connect to Redis at {REDIS_HOST}:{REDIS_PORT}.")
        sys.exit(1)

    job_id = str(uuid.uuid4())[:8]
    pod_name = None
    port_forward_process = None
    driver = None

    try:
        print(f"\n> 1: Submitting job {job_id} to queue '{JOB_QUEUE}'...")
        r.lpush(JOB_QUEUE, job_id)
        print(f"> 1: Submitting job: Success.")

        print("\n> 2: Waiting for emulator pod...")
        emulator_ip = None
        for _ in range(136):
            emulator_ip = r.hget(ACTIVE_JOBS_HASH, job_id)
            if emulator_ip:
                break
            time.sleep(1)

        if not emulator_ip:
            raise Exception("Timed out waiting for an emulator pod to become ready.")
        
        pod_name = get_pod_name_from_ip(emulator_ip)
        if not pod_name:
            raise Exception(f"Could not find pod name for IP {emulator_ip}.")
        print(f"> 2: Waiting for emulator pod: Success. Found {pod_name} at {emulator_ip}")

        print("\n> 3: Establishing connection to pod...")
        local_appium_port = 4723
        port_forward_command = ["kubectl", "port-forward", "-n", "keda", pod_name, f"{local_appium_port}:4723"]
        port_forward_process = subprocess.Popen(port_forward_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        time.sleep(15)
        
        appium_ready = False
        for i in range(10):
            try:
                r_status = requests.get(f'http://localhost:{local_appium_port}/status')
                if r_status.status_code == 200:
                    appium_ready = True
                    break
            except requests.exceptions.ConnectionError:
                print(f"Appium not ready yet, retrying ({i+1}/10)...")
            time.sleep(2)

        if not appium_ready:
            raise Exception("Appium server not responding after 10 retries.")
        print("> 3: Establishing connection to pod: Success.")

        print("\n> 4: Running Appium test...")
        options = UiAutomator2Options()
        options.platform_name = 'Android'
        options.automation_name = 'UiAutomator2'
        options.browser_name = 'Chrome'
        options.new_command_timeout = 300
        options.set_capability("appium:chromeOptions", {"w3c": True})
        options.set_capability("appium:allowInsecure", "chromedriver_autodownload")

        driver = webdriver.Remote(f'http://localhost:{local_appium_port}', options=options)
        
        time.sleep(5)
        try:
            driver.switch_to.context("NATIVE_APP")
            driver.find_element(by=By.ID, value="com.android.chrome:id/terms_accept").click()
            time.sleep(1)
            driver.find_element(by=By.ID, value="com.android.chrome:id/negative_button").click()
        except NoSuchElementException:
            pass
        
        found_webview = False
        for _ in range(30):
            webview_context = next((ctx for ctx in driver.contexts if 'CHROMIUM' in ctx), None)
            if webview_context:
                driver.switch_to.context(webview_context)
                found_webview = True
                break
            time.sleep(1)

        if not found_webview:
            raise Exception("Timed out waiting for webview context.")

        driver.get("https://www.google.com")
        time.sleep(3)
        print(f"> 4: Running Appium test: Success. Page title: {driver.title}")
        print("\n*** TEST SUCCEEDED! ***")

    except Exception as e:
        print(f"\nAn error occurred: {e}")
        input("The pod has been left running for debugging. Press Enter to clean up...")
    finally:
        print("\nCleaning up resources...")
        if driver:
            driver.quit()
        if port_forward_process:
            port_forward_process.terminate()
        
        if r and job_id:
            r.hdel(ACTIVE_JOBS_HASH, job_id)
            r.lrem(JOB_QUEUE, 0, job_id)

        if pod_name:
            subprocess.run(["kubectl", "delete", "pod", "-n", "keda", pod_name], stdout=subprocess.DEVNULL)
        print("Cleanup complete.")

# --- Main ---
if __name__ == "__main__":
    main()
