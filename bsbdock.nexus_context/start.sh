#!/bin/bash
# USE the trap if you need to also do manual cleanup after the service is stopped,
#   or need to start multiple services in the one container
trap "echo TRAPed signal" HUP INT QUIT TERM

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
echo -e "${LIGHT_BLUE}Startup of Nexus Server 1.4.0.4 [Python]${NC}"
echo -e "${LIGHT_BLUE}-------------------------------------------------------------${NC}"

echo -e ""
echo -e "-------------------------------------------------------------"
echo -e "Environment variables set:"
echo -e "-------------------------------------------------------------"

# Set default container Nexus API Port to exposed port
NEXUS_PORT="${NEXUS_PORT:-$NEXUS_CONTAINER_API_PORT}"

echo -e "NEXUS_CONFIG=$NEXUS_CONFIG"
echo -e "NEXUS_PORT=$NEXUS_PORT"
echo -e "NEXUS_ASPECT=$NEXUS_ASPECT"
echo -e "NEXUS_ROLE=$NEXUS_ROLE"
echo -e "NEXUS_LONGPOLL=$NEXUS_LONGPOLL"
echo -e "NEXUS_TIMEOUT=$NEXUS_TIMEOUT"
echo -e "NEXUS_BRIDGE=$NEXUS_BRIDGE"

echo -e ""
echo -e "-------------------------------------------------------------"
echo -e "Actual Reticulum interface configuration:"
echo -e "-------------------------------------------------------------"
# Log reticulum interface configuration
cat .reticulum/config

echo -e ""
echo -e "-------------------------------------------------------------"
echo -e "Actual Reticulum interface status:"
echo -e "-------------------------------------------------------------"
# Log reticulum interface status
rnstatus

echo -e "-------------------------------------------------------------"
echo -e "Nexus Messenger Web App NGINX configuration check and startup"
echo -e "-------------------------------------------------------------"
# Log nginx status
sudo nginx -t
sudo systemctl start nginx
sudo systemctl status nginx

#echo -e ""
#echo -e "-------------------------------------------------------------"
#echo -e "Direwolf startup"
#echo -e "-------------------------------------------------------------"
#direwolf -t 0

echo -e ""
echo -e "-------------------------------------------------------------"
echo -e "Parameters passed to server startup:"
echo -e "-------------------------------------------------------------"
echo \
  ${NEXUS_CONFIG:+--config=$NEXUS_CONFIG} \
  ${NEXUS_PORT:+--port=$NEXUS_PORT} \
  ${NEXUS_ASPECT:+--aspect=$NEXUS_ASPECT} \
  ${NEXUS_ROLE:+--role=$NEXUS_ROLE} \
  ${NEXUS_LONGPOLL:+--longpoll=$NEXUS_LONGPOLL} \
  ${NEXUS_TIMEOUT:+--timeout=$NEXUS_TIMEOUT} \
  ${NEXUS_BRIDGE:+--bridge=$NEXUS_BRIDGE}

echo -e ""
echo -e "-------------------------------------------------------------"
echo -e "Nexus Server startup"
echo -e "-------------------------------------------------------------"
# Launch nexus_server2 Server with unbuffered logs (docker takes those logs)
exec python3 -u ./nexus_server/nexus_server.py \
  ${NEXUS_CONFIG:+--config=$NEXUS_CONFIG} \
  ${NEXUS_PORT:+--port=$NEXUS_PORT} \
  ${NEXUS_ASPECT:+--aspect=$NEXUS_ASPECT} \
  ${NEXUS_ROLE:+--role=$NEXUS_ROLE} \
  ${NEXUS_LONGPOLL:+--longpoll=$NEXUS_LONGPOLL} \
  ${NEXUS_TIMEOUT:+--timeout=$NEXUS_TIMEOUT} \
  ${NEXUS_BRIDGE:+--bridge=$NEXUS_BRIDGE}
