#!/bin/bash
#################################################
# Pull image, pull repo and restart container as demon
#
source colors_set.sh

# If no template name to be used to create .env use 'default'
TEMPLATE=${1-default}

# Pull repo from git
echo -e "${PURPLE}Pull repo update from git${NC}"
bash nexus_pull.sh "$TEMPLATE"

# Pull image update from docker hub
echo -e "${PURPLE}Pull image update from docker hub${NC}"
docker compose pull

# Pull image update from docker hub
echo -e "${PURPLE}Bounce container compose${NC}"
docker compose down
docker compose up -d
