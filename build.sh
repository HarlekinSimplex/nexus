#!/bin/bash
#################################################
# Build and tag nexus_server2 container
#

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
LIGHTBLUE='\033[1;34m'
NC='\033[0m' # No Color

IMAGE_ARCH=$1
IMAGE_VERSION=$2
if [ "$IMAGE_ARCH" == "dev" ] ; then
  IMAGE_VERSION=$IMAGE_ARCH
  IMAGE_ARCH=
fi

# Check
if [ "$IMAGE_ARCH" ] && [ "$IMAGE_ARCH" != "amd64" ] && [ "$IMAGE_ARCH" != "arm64" ] && [ "$IMAGE_ARCH" != "arm" ] ||
   [ "$1" == "?" ] || [ "$1" == "-h" ] || [ "$1" == "--help" ] ; then
  echo -e ""
  echo -e "${BLUE}Usage:${NC}"
  echo -e "  build [<Arch>=amd64|arm64|arm] [<Version>=dev]"
  echo -e ""
  echo -e "${GREEN}Examples:${NC}"
  echo -e "  build.sh amd64 1.2.3"
  echo -e "  build.sh        -> build.sh amd64 dev"
  echo -e "  build.sh dev    -> build.sh amd64 dev"
  echo -e "  build.sh arm    -> build.sh arm dev"
  echo -e ""
  exit 0
fi

IMAGE_VERSION="${IMAGE_VERSION:-dev}"
IMAGE_ARCH="${IMAGE_ARCH:-amd64}"
IMAGE_OS=linux
IMAGE_TAG="$IMAGE_VERSION"_"$IMAGE_OS"-"$IMAGE_ARCH"

echo -e "${BLUE}Using ${LIGHTBLUE}$IMAGE_TAG${BLUE} as image tag.${NC}"

# Move into image context
cd ./bsbdock.nexus_context || exit

# Check if Dockerfile exists
FILE=Dockerfile_nexus_"$IMAGE_TAG"
if test -f "$FILE"; then
    echo -e "${GREEN}Dockerfile ${LIGHTBLUE}$FILE${GREEN} to build image exists.${NC}"
    echo -e "${BLUE}Building image ...${NC}"


    # Build image according given build parameters
    docker build --no-cache --build-arg CACHEBUST="$(date +%s)" \
      --tag bsbdock/nexus:"$IMAGE_TAG" \
      -f Dockerfile_nexus_"$IMAGE_TAG" .

    # Tag actual build image with given version
    docker tag bsbdock/nexus:"$IMAGE_TAG" bsbdock/nexus:"$IMAGE_VERSION"

    # Non dev image builds will be tagged as :latest and pushed to GitHub
    if [ "$IMAGE_VERSION" != "dev" ]
    then
      docker tag bsbdock/nexus:"$IMAGE_TAG" bsbdock/nexus
      docker push bsbdock/nexus:"$IMAGE_TAG"
    fi

    RESULT=$?
else
    echo -e "${YELLOW}Dockerfile $FILE to build image does ${RED}NOT${YELLOW} exists.${NC}"
    echo -e "${RED}Image build canceled.${NC}"
    RESULT=1
fi

# Return from context
cd .. || exit $RESULT
exit $RESULT
