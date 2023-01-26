#!/bin/bash
#################################################
# Clear the LXMF storage
#
source colors_set.sh

# If no template name to be used to create .env use 'default'
TEMPLATE=${1-default}

# Remove Nexus Message Store file
echo -e "${PURPLE}Remove ./nexus_root/.reticulum/$TEMPLATE/storage${NC}"
sudo rm -f -r "./nexus_root/.reticulum/$TEMPLATE/storage"
