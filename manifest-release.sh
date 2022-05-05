#!/bin/bash
#################################################
# Build and tag nexus_server2 container
#
VER=1.4.0.4
OS=linux
ARCH1=amd64
ARCH2=arm64
ARCH3=arm

echo "Version:$VER"
echo "Version:$OS"
echo "Arch 1:$ARCH1"
echo "Arch 2:$ARCH2"
echo "Arch 3:$ARCH2"

echo "Remove previous bsbdock/nexus:latest manifest"
docker manifest rm bsbdock/nexus:latest

echo "Define new latest manifest"
docker manifest create bsbdock/nexus:latest \
--amend bsbdock/nexus:$VER\_$OS-$ARCH1 \
--amend bsbdock/nexus:$VER\_$OS-$ARCH2 \
--amend bsbdock/nexus:$VER\_$OS-$ARCH3

echo "Push new latest multi architecture manifest"
docker manifest push bsbdock/nexus:latest

echo "Remove previous bsbdock/nexus:$VER version manifest"
docker manifest rm bsbdock/nexus:$VER

echo "Define new $VER manifest"
docker manifest create bsbdock/nexus:$VER \
--amend bsbdock/nexus:$VER\_$OS-$ARCH1 \
--amend bsbdock/nexus:$VER\_$OS-$ARCH2 \
--amend bsbdock/nexus:$VER\_$OS-$ARCH3

echo "Push new $VER multi architecture manifest"
docker manifest push bsbdock/nexus:$VER
