#!/bin/bash
# docker push bsbdock/nexus:1.2.1_linux-amd64
# docker push bsbdock/reticulum:2.1_linux-amd64

#################################################
# Build and tag nexus_server2 container
#
cd ./bsbdock.nexus_context
docker build --build-arg CACHEBUST=$(date +%s) --tag bsbdock/nexus:1.2.1_linux-amd64 -f Dockerfile_nexus1.2.1_linux-amd64 .
docker tag bsbdock/nexus:1.2.1_linux-amd64 bsbdock/nexus
cd ..

#################################################
# Build and tag of Reticulum only container
#
#cd ./bsbdock.reticulum_context
#docker build --tag bsbdock/reticulum:2.1_linux-amd64 -f Dockerfile_reticulum2.1_linux-amd64 .
#docker tag bsbdock/reticulum:2.1_linux-amd64 bsbdock/reticulum
#cd ..