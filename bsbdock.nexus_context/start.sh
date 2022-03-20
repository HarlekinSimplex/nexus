#!/bin/bash
# Log reticulum interface status
echo "#############################################################"
echo "# Welcome to Nexus Server"
echo "# A minimal broadcast messaging server based on Reticulum"
echo "#############################################################"

echo ""
echo "-------------------------------------------------------------"
echo " Environment variables set"
echo "-------------------------------------------------------------"
echo "NEXUS_CONFIG=$NEXUS_CONFIG"
echo "NEXUS_PORT=$NEXUS_PORT"
echo "NEXUS_ASPECT=$NEXUS_ASPECT"
echo "NEXUS_ROLE=$NEXUS_ROLE"
echo "NEXUS_LONGPOLL=$NEXUS_LONGPOLL"
echo "-------------------------------------------------------------"
echo " Parameters passed to server startup:"
echo "-------------------------------------------------------------"
echo \
${NEXUS_CONFIG:+--config=$NEXUS_CONFIG} \
${NEXUS_PORT:+--port=$NEXUS_PORT} \
${NEXUS_ASPECT:+--aspect=$NEXUS_ASPECT} \
${NEXUS_ROLE:+--role=$NEXUS_ROLE} \
${NEXUS_LONGPOLL:+--longpoll=$NEXUS_LONGPOLL}
echo ""
echo "-------------------------------------------------------------"
echo " Actual Reticulum interface configuration:"
echo "-------------------------------------------------------------"
rnstatus

echo ""
echo "-------------------------------------------------------------"
echo " Nexus Server startup"
echo "-------------------------------------------------------------"
# Launch Nexus Server with unbuffered logs (docker takes those logs)
python3 -u /bsb/Nexus/NexusServer.py \
${NEXUS_CONFIG:+--config=$NEXUS_CONFIG} \
${NEXUS_PORT:+--port=$NEXUS_PORT} \
${NEXUS_ASPECT:+--aspect=$NEXUS_ASPECT} \
${NEXUS_ROLE:+--role=$NEXUS_ROLE} \
${NEXUS_LONGPOLL:+--longpoll=$NEXUS_LONGPOLL}

echo ""
echo "-------------------------------------------------------------"
echo " Nexus Server terminated"
echo "-------------------------------------------------------------"

exit(0)