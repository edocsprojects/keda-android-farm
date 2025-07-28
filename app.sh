#!/bin/bash

# app.sh

# Initializes the Android emulator, starts the Appium server, and waits for a
# test job from the Redis queue.

# 1. Start the Android emulator in the background.
/home/androidusr/docker-android/mixins/scripts/run.sh &

# 2. Wait for the OS to fully boot before proceeding.
echo "[INFO] Waiting for emulator to fully boot..."
until adb shell getprop sys.boot_completed | grep -m 1 "1"; do
  sleep 1
done
echo "[INFO] Emulator boot complete."

# 3. Disable UI animations to improve automation speed.
adb shell settings put global window_animation_scale 0.0
adb shell settings put global transition_animation_scale 0.0
adb shell settings put global animator_duration_scale 0.0

# 4. Start the Appium server.
echo "[INFO] Starting Appium server..."
lsof -t -i :4723 | xargs -r kill -9
appium --allow-insecure chromedriver_autodownload >> /tmp/appium.log 2>&1 &

# 5. Wait for and retrieve a job from the Redis queue.
echo "[INFO] Waiting for a job from Redis on 'test_queue'..."
JOB_ID=$(redis-cli -h redis-service.keda.svc.cluster.local BRPOP test_queue 0 | tail -n 1)

if [ -z "$JOB_ID" ]; then
    echo "[ERROR] Failed to receive a job ID from Redis. Exiting."
    exit 1
fi
echo "[INFO] Picked up job: ${JOB_ID}"

# 6. Register this pod in Redis to signal that it is ready for the test.
redis-cli -h redis-service.keda.svc.cluster.local HSET active_jobs "${JOB_ID}" "${POD_IP}"

# 7. Keep the container alive until the test script terminates it.
echo "[INFO] Pod is ready and awaiting test commands."
tail -f /dev/null