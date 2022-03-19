#!/bin/bash
# Log reticulum interface status
echo "#############################################################"
echo "# Welcome to Nexus Server"
echo "# A minimal broadcast messaging server based on Reticulum"
echo "#############################################################"

echo $1 $2 $3 $4 $5 $6

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
python3 -u /bsb/Nexus/NexusServer.py

echo ""
echo "-------------------------------------------------------------"
echo " Nexus Server terminated"
echo "-------------------------------------------------------------"

exit(0)