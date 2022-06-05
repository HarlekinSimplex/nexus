#!/bin/bash
#################################################
# Reset actual repo state and repull from remote
#
sudo chown -R $(whoami) nexus*
git reset --hard
git pull
