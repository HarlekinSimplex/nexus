#!/bin/bash
# Log reticulum interface status
echo "#############################################################"
echo "# Welcome to Nexus Server"
echo "# A minimal broadcast messaging server based on Reticulum"
echo "#############################################################"

echo $NEXUS_ROOT
echo $NEXUS_ROOT_BIND
echo $NEXUS_NETWORK
echo $NEXUS_PORT_RNSAPI
echo $NEXUS_PORT_WEB
echo $NEXUS_PORT_JSONAPI

echo

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
python3 -u /bsb/Nexus/NexusServer.py $1 $2 $3 $4 $5

echo ""
echo "-------------------------------------------------------------"
echo " Nexus Server terminated"
echo "-------------------------------------------------------------"

exit(0)