#!/bin/bash
#################################################
# Reset actual repo state and repull from remote
#
sudo chown -R "$(whoami)" nexus*
git reset --hard
git pull

TARGET=${1-default}

grep "$TARGET" .env_master | sed "s/$TARGET://g" >.env

