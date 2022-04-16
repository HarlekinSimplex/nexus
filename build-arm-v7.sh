#!/bin/bash
#################################################
# Build and tag nexus_server container
#
cd ./bsbdock.nexus_context
docker build --no-cache --build-arg CACHEBUST=$(date +%s) --tag bsbdock/nexus:1.3.0.3_linux-arm-v7 -f Dockerfile_nexus1.3.0.3_linux-arm-v7 .
docker tag bsbdock/nexus:1.3.0.3_linux-arm-v7 bsbdock/nexus
# docker push bsbdock/nexus:1.3.0.3_linux-arm-v7
cd ..
