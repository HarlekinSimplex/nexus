#!/bin/bash
#################################################
# Clear Nexus message store
#
source colors_set.sh

# If no template name to be used to create .env use 'default'
TEMPLATE=${1-default}

# Bounce docker (here down) if option is given
if [ "$1" == "-d" ] ; then
  # Shut down actual container composition
  echo -e "${PURPLE}Shut down actual container composition${NC}"
  docker compose down
fi

# Remove Nexus Message Store file
echo -e "${PURPLE}Remove ./nexus_root/.nexus/storage/messages.umspack${NC}"
sudo rm -f -r "./nexus_root/.reticulum/$TEMPLATE/storage"

# Bounce docker (here up) if option is given
if [ "$1" == "-d" ] ; then
  # Launch container composition
  echo -e "${PURPLE}Launch container composition${NC}"
  docker compose up -d
fi