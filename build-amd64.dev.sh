#!/bin/bash
#################################################
# Build and tag nexus_server2 container
#
VER=dev
OS=linux
ARCH=amd64

cd ./bsbdock.nexus_context
docker build --no-cache --build-arg CACHEBUST=$(date +%s) --tag bsbdock/nexus:$VER\_$OS-$ARCH -f Dockerfile_nexus$VER\_$OS-$ARCH .
#docker tag bsbdock/nexus:$VER_$OS-$ARCH bsbdock/nexus
#docker push bsbdock/nexus:$VER_$OS-$ARCH
cd ..
