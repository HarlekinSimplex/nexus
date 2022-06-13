#!/bin/bash
#############################################################
# Replace actual .env with '#default:' tagged content from .env_master
# If other env tamplates are included in .env_master as well its tag can be used as parameter $1 to this script
#
bash colors_set.sh

TEMPLATE=${1-default}

echo -e "${BLUE}Create .env from .env_master using template name '#$TEMPLATE:'${NC}"
grep "#$TEMPLATE:" .env_master | sed "s/#$TEMPLATE://g" >.env

