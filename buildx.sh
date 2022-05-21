#!/bin/bash
#################################################
# Build and tag nexus_server2 container
#

export RED='\033[0;31m'
export LIGHT_RED='\033[1;31m'
export YELLOW='\033[1;33m'
export GREEN='\033[0;32m'
export LIGHT_GREEN='\033[1;32m'
export BLUE='\033[0;34m'
export LIGHT_BLUE='\033[1;34m'
export CYAN='\033[0;36m'
export NC='\033[0m' # No Color

USE_CACHE=

IMAGE_ARCH=$1
IMAGE_VERSION=$2

# Check if we should disable cache
if [ "$1" == "-nc" ] ; then
  IMAGE_ARCH=$2
  IMAGE_VERSION=$3
  USE_CACHE=NO
fi

# Check if we should enable cache
if [ "$1" == "-c" ] ; then
  IMAGE_ARCH=$2
  IMAGE_VERSION=$3
  USE_CACHE=YES
fi

# Check if arch was not given but dev
if [ "$IMAGE_ARCH" == "dev" ] ; then
  IMAGE_VERSION=$IMAGE_ARCH
  IMAGE_ARCH=
fi

# Check for version build unlike dev to build without cache
if [ -z "$USE_CACHE" ] && [ "$IMAGE_VERSION" ] && [ "$IMAGE_VERSION" != "dev" ] ; then
  USE_CACHE=NO
fi

# Set some defaults if still no set
USE_CACHE="${USE_CACHE:-YES}"
IMAGE_VERSION="${IMAGE_VERSION:-dev}"
IMAGE_ARCH="${IMAGE_ARCH:-amd64}"
IMAGE_OS=linux
IMAGE_TAG="$IMAGE_VERSION"_"$IMAGE_OS"-"$IMAGE_ARCH"
BUILD_FILE=dev_"$IMAGE_OS"-"$IMAGE_ARCH"

# Check
if [ "$IMAGE_ARCH" ] && [ "$IMAGE_ARCH" != "amd64" ] && [ "$IMAGE_ARCH" != "arm64" ] && [ "$IMAGE_ARCH" != "arm" ] ||
   [ "$1" == "?" ] || [ "$1" == "-h" ] || [ "$1" == "--help" ] ; then
  echo -e ""
  echo -e "${BLUE}Usage:${NC}"
  echo -e "  build [-c|-nc] [<Arch>=amd64|arm64|arm] [<Version>=dev]"
  echo -e ""
  echo -e "${GREEN}Examples:${NC}"
  echo -e "  build.sh amd64 1.2.3      -> build 1.2.3_linux-amd64 (using no cache)"
  echo -e "  build.sh -c amd64 1.2.3   -> build 1.2.3_linux-amd64 (using cache)"
  echo -e "  build.sh                  -> build.sh amd64 dev (using no cache)"
  echo -e "  build.sh dev              -> build.sh amd64 dev (using no cache)"
  echo -e "  build.sh arm              -> build.sh arm dev (using cache)"
  echo -e ""
  echo -e "With version 'dev' cache usage is activated, otherwise not."
  echo -e "However, Cache usage is overruled by -c or -nc if specified."
  echo -e ""
  exit 0
fi

# echo Cache:$USE_CACHE
# echo IMAGE_ARCH:$IMAGE_ARCH
# echo IMAGE_VERSION:$IMAGE_VERSION
# exit

echo -e "${BLUE}Using ${CYAN}$IMAGE_TAG${BLUE} as image tag.${NC}"

# Move into image context
cd ./bsbdock.nexus_context || exit

# Check if Dockerfile exists
FILE=Dockerfile_nexus_"$BUILD_FILE"
if test -f "$FILE"; then
    echo -e "${GREEN}Dockerfile ${CYAN}$FILE${GREEN} to build image exists.${NC}"

    # Set --no-cache if version is dev
    CACHE_OPT=
    if  [ "$USE_CACHE" == "NO" ] ; then
      CACHE_OPT=--no-cache
      echo -e "${BLUE}Using option ${YELLOW}--no-cache${BLUE} during build.${NC}"
    fi

    echo -e "${BLUE}Building image ...${NC}"

    # Build image according given build parameters
    docker buildx build --build-arg CACHEBUST="$(date +%s)" $CACHE_OPT \
      --tag bsbdock/nexus:"$IMAGE_TAG" \
      -f Dockerfile_nexus_"$BUILD_FILE" .

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
