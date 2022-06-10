#!/bin/bash
#############################################################
# Replace actual .env with '#default:' tagged content from .env_master
# If other env tamplates are included in .env_master as well its tag can be used as parameter $1 to this script
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

TEMPLATE=${1-default}

echo -e "${BLUE}Create .env from .env_master using template name '#$TEMPLATE:'${NC}"
grep "#$TEMPLATE:" .env_master | sed "s/#$TEMPLATE://g" >.env

