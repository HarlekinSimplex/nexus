#!/bin/bash
#################################################
# Pull image, pull repo and restart container as demon
#
bash colors_set.sh

# If no template name to be used to create .env use 'default'
TEMPLATE=${1-default}

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
