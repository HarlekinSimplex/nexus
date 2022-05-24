#!/bin/bash
# USE the trap if you need to also do manual cleanup after the service is stopped,
#   or need to start multiple services in the one container
# trap "echo TRAPed signal" HUP INT QUIT TERM

# Exit on error
set -e

# Set color tags for use with 'echo -e'
export RED='\033[0;31m'
export LIGHT_RED='\033[1;31m'
export YELLOW='\033[1;33m'
export GREEN='\033[0;32m'
export LIGHT_GREEN='\033[1;32m'
export BLUE='\033[0;34m'
export LIGHT_BLUE='\033[1;34m'
export CYAN='\033[0;36m'
export NC='\033[0m' # No Color

echo -e ""
echo -e "${LIGHT_BLUE}-------------------------------------------------------------${NC}"
echo -e "${LIGHT_BLUE}Startup of Nexus Server [Legacy]${NC}"
echo -e "${LIGHT_BLUE}-------------------------------------------------------------${NC}"

echo -e ""
echo -e "-------------------------------------------------------------"
echo -e "Nexus Server startup"
echo -e "-------------------------------------------------------------"
# Launch nexus_server2 Server with unbuffered logs (docker takes those logs)
exec python3 -u ./nexus_server/nexus_server.py \
  ${NEXUS_CONFIG:+--config=$RNS_CONFIG} \
  ${NEXUS_PORT:+--port=$NEXUS_PORT} \
  ${NEXUS_ASPECT:+--aspect=$NEXUS_ASPECT} \
  ${NEXUS_ROLE:+--role=$NEXUS_ROLE} \
  ${NEXUS_LONGPOLL:+--longpoll=$NEXUS_LONGPOLL} \
  ${NEXUS_TIMEOUT:+--timeout=$NEXUS_TIMEOUT} \
  ${NEXUS_BRIDGE:+--bridge=$NEXUS_BRIDGE}
