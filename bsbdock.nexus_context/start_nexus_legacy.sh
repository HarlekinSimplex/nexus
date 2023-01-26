#!/bin/bash
# USE the trap if you need to also do manual cleanup after the service is stopped,
#   or need to start multiple services in the one container
# trap "echo TRAPed signal" HUP INT QUIT TERM

# Exit on error
set -e

echo -e ""
echo -e "${LIGHT_BLUE}-------------------------------------------------------------${NC}"
echo -e "${LIGHT_BLUE}Startup of Nexus Server [Legacy]${NC}"
echo -e "${LIGHT_BLUE}-------------------------------------------------------------${NC}"

# Launch nexus_server2 Server with unbuffered logs (docker takes those logs)
if [ "$NEXUS_DYNAMIC_MASTER" == "True" ] ; then
	export NEXUS_DYNAMIC_MASTER_FLAG="--dynamicmaster"
else
	export NEXUS_DYNAMIC_MASTER_FLAG=
fi

exec python3 -u ./nexus_server/nexus_server.py \
  ${NEXUS_CONFIG:+--config=$RNS_CONFIG} \
  ${NEXUS_PORT:+--port=$NEXUS_PORT} \
  ${NEXUS_ASPECT:+--aspect=$NEXUS_ASPECT} \
  ${NEXUS_ROLE:+--role=$NEXUS_ROLE} \
  ${NEXUS_LONGPOLL:+--longpoll=$NEXUS_LONGPOLL} \
  ${NEXUS_SHORTPOLL:+--shortpoll=$NEXUS_SHORTPOLL} \
  ${NEXUS_TIMEOUT:+--timeout=$NEXUS_TIMEOUT} \
  ${NEXUS_POSTMASTER:+--postmaster=$NEXUS_POSTMASTER} \
  "${NEXUS_DYNAMIC_MASTER_FLAG}" \
  ${NEXUS_BRIDGE:+--bridge=$NEXUS_BRIDGE}
