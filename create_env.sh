#!/bin/bash
#############################################################
# Replace actual .env with '#default:' tagged content from .env_master
# If other env tamplates are included in .env_master as well its tag can be used as parameter $1 to this script
#
TEMPLATE=${1-default}
echo "Creating .env from .env_master with target filer '#TEMPLATE:'"
grep "#TEMPLATE" .env_master | sed "s/#TEMPLATE://g" >.env

