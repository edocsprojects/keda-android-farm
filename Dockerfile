# Dockerfile

#1. Start with budtmo/docker-android verison 14.0
FROM budtmo/docker-android:emulator_14.0

# 2. Enchancements for performance
ENV EMULATOR_ARGS="-no-snapshot-load -no-boot-anim -no-audio -no-window -accel on -engine qemu2 -dns-server 8.8.8.8"

# 3. Switch user for installation of tools
USER root

# 4. Add redis, lsof, and curl
RUN apt-get update && apt-get install -y redis-tools lsof curl

# 5. Switch user to default
USER androidusr

# 6. Copy over app.sh
COPY --chmod=755 app.sh /opt/app.sh

# 7. Set app.sh as default command
ENTRYPOINT ["/opt/app.sh"]