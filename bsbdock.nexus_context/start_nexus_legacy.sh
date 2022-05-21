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

# Log reticulum interface status
echo -e ""
echo -e "${LIGHT_BLUE}-------------------------------------------------------------${NC}"
echo -e "${LIGHT_BLUE}Startup of Nexus Server [Legacy]${NC}"
echo -e "${LIGHT_BLUE}-------------------------------------------------------------${NC}"

#-------------------------------------------------------------------------------------------------

echo -e ""
echo -e "-------------------------------------------------------------"
echo -e "Environment variables set:"
echo -e "-------------------------------------------------------------"

echo -e "${LIGHT_BLUE}Reticulum configuration environment:${NC}"
echo -e "RNS_CONFIG=$RNS_CONFIG"
echo -e "RNS_AUTOSTART=$RNS_AUTOSTART"

echo -e ""
echo -e "${LIGHT_BLUE}Nomadnetwork configuration environment:${NC}"
echo -e "NOMADNET_CONFIG=$NOMADNET_CONFIG"
echo -e "NOMADNET_AUTOSTART=$NOMADNET_AUTOSTART"

echo -e ""
echo -e "${LIGHT_BLUE}Direwolf configuration environment:${NC}"
echo -e "DIREWOLF_CONFIG=$DIREWOLF_CONFIG"
echo -e "DIREWOLF_AUTOSTART=$DIREWOLF_AUTOSTART"

echo -e ""
echo -e "${LIGHT_BLUE}Soundmodem configuration environment:${NC}"
echo -e "SOUNDMODEM_CONFIG=$SOUNDMODEM_CONFIG"
echo -e "SOUNDMODEM_AUTOSTART=$SOUNDMODEM_AUTOSTART"

echo -e ""
echo -e "${LIGHT_BLUE}Django configuration environment:${NC}"
echo -e "DJANGO_SUPERUSER_USERNAME=$DJANGO_SUPERUSER_USERNAME"
echo -e "DJANGO_SUPERUSER_PASSWORD=$DJANGO_SUPERUSER_PASSWORD"
echo -e "DJANGO_SUPERUSER_EMAIL=$DJANGO_SUPERUSER_EMAIL"
echo -e "DJANGO_LOG_LEVEL=$DJANGO_LOG_LEVEL"

echo -e ""
echo -e "${LIGHT_BLUE}Nexus configuration environment:${NC}"
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
cat "$RNS_CONFIG"/config

if [ "$RNS_AUTOSTART" != "False" ] ; then
  echo -e ""
  echo -e "-------------------------------------------------------------"
  echo -e "Autostart RNS as service"
  echo -e "-------------------------------------------------------------"
  # Log reticulum interface status
  rnsd -s &
  sleep 1
  echo "RNS PID="$(pgrep rnsd)
fi

echo -e ""
echo -e "-------------------------------------------------------------"
echo -e "Actual RNS interface status"
echo -e "-------------------------------------------------------------"
rnstatus

if [ "$NOMADNET_AUTOSTART" != "False" ] ; then
  echo -e ""
  echo -e "-------------------------------------------------------------"
  echo -e "Autostart Nomadnetwork as service"
  echo -e "-------------------------------------------------------------"
  # Log reticulum interface status
  nomadnet --daemon &
  sleep 1
  echo "nomadnet PID="$(pgrep nomadnet)
fi

if [ "$DIREWOLF_AUTOSTART" != "False" ] ; then
  echo -e ""
  echo -e "-------------------------------------------------------------"
  echo -e "Autostart Direwolf"
  echo -e "-------------------------------------------------------------"
  direwolf -t 0 &
  sleep 1
  echo "direwolf PID=""$(pgrep direwolf)"
fi

echo -e ""
echo -e "-------------------------------------------------------------"
echo -e "Nexus Messenger Web App NGINX configuration check and startup"
echo -e "-------------------------------------------------------------"
# Log nginx status
sudo nginx -t
sudo systemctl start nginx
sudo systemctl status nginx

#-------------------------------------------------------------------------------------------------

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
