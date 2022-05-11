#!/bin/bash
#################################################
# Build and tag nexus_server2 container
#

IMAGE_VERSION=$1
IMAGE_ARCH=$2

# Check
if [ "$IMAGE_ARCH" ] && [ "$IMAGE_ARCH" != "amd64" ] && [ "$IMAGE_ARCH" != "arm64" ] && [ "$IMAGE_ARCH" != "arm" ]
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

IMAGE_VERSION="${IMAGE_VERSION:-dev}"
IMAGE_ARCH="${IMAGE_ARCH:-amd64}"
IMAGE_OS=linux
IMAGE_TAG="$IMAGE_VERSION"_"$IMAGE_OS"-"$IMAGE_ARCH"

echo "$IMAGE_TAG"

exit

cd ./bsbdock.nexus_context || exit
docker build --no-cache --build-arg CACHEBUST="$(date +%s)" \
  --tag bsbdock/nexus:"$IMAGE_TAG" \
  -f Dockerfile_nexus_"$IMAGE_TAG" .
docker tag bsbdock/nexus:"$IMAGE_TAG" bsbdock/nexus:"$IMAGE_VERSION"

if [ "$IMAGE_VERSION" != "dev" ]
then
  docker tag bsbdock/nexus:"$IMAGE_TAG" bsbdock/nexus
  docker push bsbdock/nexus:"$IMAGE_TAG"
fi

cd .. || exit

