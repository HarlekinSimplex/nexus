#!/bin/bash
#################################################
# Build and tag nexus_server2 container
#
VERSION=dev
OS=linux
ARCH=amd64

cd ./bsbdock.nexus_context
docker build --no-cache --build-arg CACHEBUST=$(date +%s) --tag bsbdock/nexus:$VERSION_$OS-$ARCH -f Dockerfile_nexus$VERSION_$OS-$ARCH .
#docker tag bsbdock/nexus:$VERSION_$OS-$ARCH bsbdock/nexus
#docker push bsbdock/nexus:$VERSION_$OS-$ARCH
cd ..
