#!/bin/bash
#################################################
# Reset actual repo state and repull from remote
#
sudo chown -R "$(whoami)" nexus*
git reset --hard
git pull

TARGET=${1-default}
echo "Creating .env from .env_master with target filer $TARGET"
grep "#$TARGET" .env_master | sed "s/#$TARGET://g" >.env

