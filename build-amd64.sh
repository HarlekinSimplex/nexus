#!/bin/bash
# docker buildx build --push --no-cache --tag bsbdock/nexus1.0_linux-amd64 -f Dockerfile_nexus1.0_linux-amd64 .
cd ./bsbdock.nexus_context
docker buildx build --tag bsbdock/nexus -f Dockerfile_nexus1.0_linux-amd64 .
cd ../bsbdock.reticulum_context
docker buildx build --tag bsbdock/nexus -f Dockerfile_nexus1.0_linux-amd64 .