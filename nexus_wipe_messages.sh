#!/bin/bash
#################################################
# Clear Nexus message store
#
source colors_set.sh

# If no template name to be used to create .env use 'default'
TEMPLATE=${1-default}

# Shut down actual container composition
echo -e "${PURPLE}Shut down actual container composition${NC}"
docker compose down

# Remove Nexus Message Store file
echo -e "${PURPLE}Remove ./nexus_root/.nexus/storage/messages.umspack${NC}"
rm ./nexus_root/.nexus/storage/messages.umsgpack

# Launch container composition
echo -e "${PURPLE}Launch container composition${NC}"
docker compose up -d
