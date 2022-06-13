#!/bin/bash
#################################################
# Reset repo state and pull actual version from Git
# afterwards create .env from .env_master default template or use given template name
#
source colors_set.sh

# If no template name to be used to create .env use 'default'
TEMPLATE=${1-default}

# Change owner of nexus_root* directories back to actual user
echo -e "${LIGH_CYAN}Changing owner of nexus_root* to '$(whoami)'${NC}"
sudo chown -R "$(whoami)" nexus_root*
# Reset local repository
echo -e "${LIGH_CYAN}Reset local nexus repository${NC}"
git reset --hard
# Update local repository
echo -e "${LIGH_CYAN}Pull actual state from git${NC}"
git pull

if [ "$TEMPLATE" != "NO_ENV" ] ; then
  # Replace .env with template pulled from .env_master
  bash ./create_env.sh "$TEMPLATE"
else
  echo -e "${LIGH_CYAN}Environment configuration file .env has not been changed${NC}"
fi
