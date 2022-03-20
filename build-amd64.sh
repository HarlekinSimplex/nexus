#!/bin/bash
# docker push bsbdock/nexus:1.0_linux-amd64
# docker push bsbdock/reticulum:2.1_linux-amd64

cd ./bsbdock.nexus_context
docker build --tag bsbdock/nexus:1.0_linux-amd64 -f Dockerfile_nexus1.0_linux-amd64 .
docker tag bsbdock/nexus:1.0_linux-amd64 bsbdock/nexus
cd ..

cd ./bsbdock.reticulum_context
docker build --tag bsbdock/reticulum:2.1_linux-amd64 -f Dockerfile_reticulum2.1_linux-amd64 .
docker tag bsbdock/reticulum:2.1_linux-amd64 bsbdock/reticulum
cd ..