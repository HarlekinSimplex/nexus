#!/bin/bash
# docker push bsbdock/nexus:1.3.0.2_linux-amd64
# docker push bsbdock/reticulum:2.1_linux-amd64

#################################################
# Build and tag nexus_server2 container
#
cd ./bsbdock.nexus_context
docker build --build-arg CACHEBUST=$(date +%s) --tag bsbdock/nexus:1.3.0.2_linux-amd64 -f Dockerfile_nexus1.3.0.2_linux-amd64 .
docker tag bsbdock/nexus:1.3.0.2_linux-amd64 bsbdock/nexus
cd ..
