#!/bin/bash
#################################################
# Reset repo state and pull actual version from Git
# afterwards create .env from .env_master default template or use given template name
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

# Change owner of nexus_root* directories back to actual user
echo -e "${BLUE}Changing owner of nexus_root* to '$(whoami)'${NC}"
sudo chown -R "$(whoami)" nexus_root*
# Reset local repository
echo -e "${BLUE}Reset local nexus repository${NC}"
git reset --hard
# Update local repository
echo -e "${BLUE}Pull actual state from git${NC}"
git pull

if [ "$TEMPLATE" != "NO_ENV" ] ; then
  # Replace .env with template pulled from .env_master
  bash ./create_env.sh "$TEMPLATE"
else
  echo -e "${BLUE}Environment configuration file .env has not been changed${NC}"
fi
