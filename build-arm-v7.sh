#!/bin/bash
# docker push bsbdock/nexus:1.0_linux-arm-v7
# docker push bsbdock/reticulum:2.1_linux-arm-v7

#################################################
# Build and tag nexus_server container
#
cd ./bsbdock.nexus_context
docker build --tag bsbdock/nexus:1.0_linux-arm-v7 -f Dockerfile_nexus1.0_linux-arm-v7 .
docker tag bsbdock/nexus:1.0_linux-arm-v7 bsbdock/nexus
cd ..

#################################################
# Build and tag of Reticulum only container
#
#cd ./bsbdock.reticulum_context
#docker build --tag bsbdock/reticulum:2.1_linux-arm-v7 -f Dockerfile_reticulum2.1_linux-arm-v7 .
#docker tag bsbdock/reticulum:2.1_linux-arm-v7 bsbdock/reticulum
#cd ..