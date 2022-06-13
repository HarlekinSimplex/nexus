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

echo -e "${LIGHT_CYAN}Update nexus instance ${LIGHT_PURPLE}nexus-reticulum${NC}"
cd ~/*reticulum
bash nexus_update.sh cb_retiuculum

echo -e "${LIGHT_CYAN}Update nexus instance ${LIGHT_PURPLE}nexus-home${NC}"
cd ~/*home
bash nexus_update.sh cb_home

echo -e "${LIGHT_CYAN}Update nexus instance ${LIGHT_PURPLE}nexus-delta${NC}"
cd ~/*delta
bash nexus_update.sh cb_delta

echo -e "${LIGHT_CYAN}Update nexus instance ${LIGHT_PURPLE}nexus-cockpit${NC}"
cd ~/*cockpit
bash nexus_update.sh cb_cockpit

echo -e "${LIGHT_CYAN}Update nexus instance ${LIGHT_PURPLE}nexus-dev${NC}"
cd ~/*dev
bash nexus_update.sh cb_dev

echo -e "${LIGHT_CYAN}Update nexus instance ${LIGHT_PURPLE}nexus-hub${NC}"
cd ~/*hub
bash nexus_update.sh cb_hub
