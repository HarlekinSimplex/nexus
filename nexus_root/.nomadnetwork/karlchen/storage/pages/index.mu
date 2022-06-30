#!/bin/bash
#################################################
# Set end xport color env variables
#
cat $NOMADNET_CONFIG/storage/pages/banner.txt

echo " "
echo " "
echo " Reticulum configuration environment:"
echo " -------------------------------------------------------------"
echo " RNS_AUTOSTART=$RNS_AUTOSTART"

echo " "
echo " Nomadnetwork configuration environment:"
echo " -------------------------------------------------------------"
echo " NOMADNET_AUTOSTART=$NOMADNET_AUTOSTART"
echo " NOMADNET_INDEX_SCRIPT=$NOMADNET_INDEX_SCRIPT"

echo " "
echo " Direwolf configuration environment:"
echo " -------------------------------------------------------------"
echo " DIREWOLF_AUTOSTART=$DIREWOLF_AUTOSTART"
echo " DIREWOLF_OPTIONS=$DIREWOLF_OPTIONS"
echo " DIREWOLF_INSTANCES=$DIREWOLF_INSTANCES"

echo " "
echo " Nginx configuration environment:"
echo " -------------------------------------------------------------"
echo " NGINX_AUTOSTART=$NGINX_AUTOSTART"

echo " "
echo " Nexus backend autostart:"
echo " -------------------------------------------------------------"
echo " NEXUS_BACKEND_AUTOSTART=$NEXUS_BACKEND_AUTOSTART"

echo " "
echo " Nexus configuration environment:"
echo " -------------------------------------------------------------"
echo " NEXUS_PORT=$NEXUS_PORT"
echo " NEXUS_ASPECT=$NEXUS_ASPECT"
echo " NEXUS_ROLE=$NEXUS_ROLE"
echo " NEXUS_LONGPOLL=$NEXUS_LONGPOLL"
echo " NEXUS_TIMEOUT=$NEXUS_TIMEOUT"
echo " NEXUS_BRIDGE=$NEXUS_BRIDGE"

echo
echo " -------------------------------------------------------------"
echo " RNS Interface Status"
echo " ------------------------------------------------------------"
sudo rnstatus --config $RNS_CONFIG 2>&1
