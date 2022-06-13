#!/bin/bash
#################################################
# Pull image, pull repo and restart container as demon
#
source colors_set.sh

# If no template name to be used to create .env use 'default'
TEMPLATE=${1-default}

# Pull repo from git
echo -e "${PURPLE}Pull actual repo update from git and create .env from template '$TEMPLATE'${NC}"
bash nexus_pull.sh "$TEMPLATE"

# Shut down container composition
echo -e "${PURPLE}Shut down container composition${NC}"
docker compose down

# Pull image update from docker hub
echo -e "${PURPLE}Pull image update from docker hub${NC}"
docker compose pull

# Launch container composition
echo -e "${PURPLE}Launch container composition${NC}"
docker compose up -d
