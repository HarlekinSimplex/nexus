#!/bin/bash
#################################################
# Set end xport color env variables
#

export RED='\033[0;31m'
export LIGHT_RED='\033[1;31m'
export GREEN='\033[0;32m'
export LIGHT_GREEN='\033[1;32m'
export YELLOW='\033[0;33m'
export LIGHT_YELLOW='\033[1;33m'
export BLUE='\033[0;34m'
export LIGHT_BLUE='\033[1;34m'
export PURPLE='\033[0;35m'
export LIGHT_PURPLE='\033[1;35m'
export CYAN='\033[0;36m'
export LIGHT_CYAN='\033[1;36m'
export NC='\033[0m' # No Color

echo -e "${LIGHT_BLUE}Update nexus instance ${LIGHT_GREEN}nexus-reticulum${NC}"
cd ~/*reticulum
pwd
bash nexus_update.sh cb_reticulum

echo -e "${LIGHT_BLUE}Update nexus instance ${LIGHT_GREEN}nexus-home${NC}"
cd ~/*home
pwd
bash nexus_update.sh cb_home

echo -e "${LIGHT_BLUE}Update nexus instance ${LIGHT_GREEN}nexus-delta${NC}"
cd ~/*delta
pwd
bash nexus_update.sh cb_delta

echo -e "${LIGHT_BLUE}Update nexus instance ${LIGHT_GREEN}nexus-cockpit${NC}"
cd ~/*cockpit
pwd
bash nexus_update.sh cb_cockpit

echo -e "${LIGHT_BLUE}Update nexus instance ${LIGHT_GREEN}nexus-dev${NC}"
cd ~/*dev
pwd
bash nexus_update.sh cb_dev

echo -e "${LIGHT_BLUE}Update nexus instance ${LIGHT_GREEN}nexus-hub${NC}"
cd ~/*hub
pwd
bash nexus_update.sh cb_hub
