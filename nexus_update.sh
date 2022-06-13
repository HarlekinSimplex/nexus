#!/bin/bash
#################################################
# Pull image, pull repo and restart container as demon
#

# If no template name to be used to create .env use 'default'
TEMPLATE=${1-default}

export RED='\033[0;31m'
export LIGHT_RED='\033[1;31m'
export YELLOW='\033[1;33m'
export GREEN='\033[0;32m'
export LIGHT_GREEN='\033[1;32m'
export BLUE='\033[0;34m'
export LIGHT_BLUE='\033[1;34m'
export CYAN='\033[0;36m'
export NC='\033[0m' # No Color

# Pull repo from git
echo -e "${CYAN}Pull repo update from git{NC}"
bash nexus_pull.sh "$TEMPLATE"

# Pull image update from docker hub
echo -e "${CYAN}Pull image update from docker hub{NC}"
docker compose pull

# Pull image update from docker hub
echo -e "${CYAN}Bounce container compose{NC}"
docker compose down
docker compose up -d
