#!/bin/bash
#################################################
# Build and tag nexus_server2 container
#
VER=$1
OS=linux
ARCH=$2

if [ -z "$1" ] || { [ "$2" != "arm64" ] && [ "$2" != "arm" ] ; }
then
  echo ""
  echo "Usage:"
  echo "  build <Version> [<Arch>=amd64|arm64|arm]"
  echo "Examples:"
  echo "  build.sh 2.0.0 amd64"
  echo "  build.sh dev"
fi

exit

VER="${VER:-dev}"
OS="${OS:-linux}"
ARCH="${OS:-amd64}"

TAG="$VER"_"$OS"-"$ARCH"

cd ./bsbdock.nexus_context || exit
docker build --no-cache --build-arg CACHEBUST="$(date +%s)" \
  --tag bsbdock/nexus:"$TAG" \
  -f Dockerfile_nexus_"$TAG" .
docker tag bsbdock/nexus:"$TAG" bsbdock/nexus:"$1"

if [ "$VER" != "dev" ]
then
  docker tag bsbdock/nexus:"$TAG" bsbdock/nexus
  docker push bsbdock/nexus:"$TAG"
fi

cd .. || exit

