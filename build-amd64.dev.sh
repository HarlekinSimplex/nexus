#!/bin/bash
# docker push bsbdock/nexus:dev_linux-amd64
# docker push bsbdock/reticulum:dev_linux-amd64

#################################################
# Build and tag nexus_server2 container
#
cd ./bsbdock.nexus_context
docker build --build-arg CACHEBUST=$(date +%s) --tag bsbdock/nexus:dev_linux-amd64 -f Dockerfile_nexusdev_linux-amd64 .
docker tag bsbdock/nexus:dev_linux-amd64 bsbdock/nexus
cd ..
