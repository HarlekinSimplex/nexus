#!/bin/bash
#################################################
# Build and tag nexus_server2 container
#

# Check
if [ "$2" ] && [ "$2" != "amd64" ] && [ "$2" != "arm64" ] && [ "$2" != "arm" ]
then
  echo ""
  echo "Usage:"
  echo "  build [<Version>=dev] [<Arch>=amd64|arm64|arm]"
  echo ""
  echo "Examples:"
  echo "  build.sh"
  echo "  build.sh 2.0.0"
  echo "  build.sh 2.0.0 arm64"
  echo ""
fi

VER="${$1:-dev}"
ARCH="${$2:-amd64}"
OS=linux
TAG="$VER"_"$OS"-"$ARCH"

echo $TAG

exit

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

