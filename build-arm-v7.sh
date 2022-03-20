#!/bin/bash
# docker buildx build --push --no-cache --tag bsbdock/nexus1.0_linux-amd64 -f Dockerfile_nexus1.0_linux-amd64 .

cd ./bsbdock.nexus_context
docker build --tag bsbdock/nexus:1.0_linux-arm-v7 -f Dockerfile_nexus1.0_linux-arm-v7 .

cd ./bsbdock.reticulum_context
docker build --tag bsbdock/reticulum:2.1_linux-arm-v7 -f Dockerfile_reticulum2.1_linux-arm-v7 .
