#!/bin/bash
#################################################
# Set end xport color env variables
#
cat $NOMADNET_CONFIG/storage/pages/banner.txt

echo
echo " -------------------------------------------------------------"
echo " Configured node environment:"
echo " -------------------------------------------------------------"
echo
echo " RNS_AUTOSTART=$RNS_AUTOSTART"
echo " NOMADNET_AUTOSTART=$NOMADNET_AUTOSTART"
echo " NGINX_AUTOSTART=$NGINX_AUTOSTART"
echo " -------------------------------------------------------------"
echo " NEXUS_PORT_RNSAPI=$NEXUS_PORT_RNSAPI"
echo " NEXUS_PORT_WEB=$NEXUS_PORT_WEB"
echo " NEXUS_PORT_JSONAPI=$NEXUS_PORT_JSONAPI"
echo " -------------------------------------------------------------"
echo " NEXUS_ASPECT=$NEXUS_ASPECT"
echo " NEXUS_ROLE=$NEXUS_ROLE"
echo " NEXUS_LONGPOLL=$NEXUS_LONGPOLL"
echo " NEXUS_SHORTPOLL=$NEXUS_SHORTPOLL"
echo " NEXUS_POSTMASTER=$NEXUS_POSTMASTER"
echo " NEXUS_TIMEOUT=$NEXUS_TIMEOUT"
echo " NEXUS_BRIDGE=$NEXUS_BRIDGE"
echo
echo " -------------------------------------------------------------"
echo " RNS Interface Status"
echo " ------------------------------------------------------------"
sudo rnstatus --config $RNS_CONFIG 2>&1
