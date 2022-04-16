#!/bin/bash
#################################################
# Build and tag nexus_server2 container
#
cd ./bsbdock.nexus_context
docker build --no-cache --build-arg CACHEBUST=$(date +%s) --tag bsbdock/nexus:1.3.0.3_linux-amd64 -f Dockerfile_nexus1.3.0.3_linux-amd64 .
docker tag bsbdock/nexus:1.3.0.3_linux-amd64 bsbdock/nexus
# docker push bsbdock/nexus:1.3.0.3_linux-amd64
cd ..
