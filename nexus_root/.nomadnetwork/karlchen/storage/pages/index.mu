#!/bin/bash
#################################################
# Set end xport color env variables
#
cat $NOMADNET_CONFIG/storage/pages/banner.txt

echo -e ""
echo -e "Environment variables set:"
echo -e "-------------------------------------------------------------"

echo -e "${LIGHT_BLUE}Reticulum configuration environment:${NC}"
echo -e "RNS_CONFIG=$RNS_CONFIG"
echo -e "RNS_AUTOSTART=$RNS_AUTOSTART"

echo -e ""
echo -e "${LIGHT_BLUE}Nomadnetwork configuration environment:${NC}"
echo -e "NOMADNET_CONFIG=$NOMADNET_CONFIG"
echo -e "NOMADNET_AUTOSTART=$NOMADNET_AUTOSTART"
echo -e "NOMADNET_INDEX_SCRIPT=$NOMADNET_INDEX_SCRIPT"

echo -e ""
echo -e "${LIGHT_BLUE}Direwolf configuration environment:${NC}"
echo -e "DIREWOLF_CONFIG=$DIREWOLF_CONFIG"
echo -e "DIREWOLF_OPTIONS=$DIREWOLF_OPTIONS"
echo -e "DIREWOLF_INSTANCES=$DIREWOLF_INSTANCES"
echo -e "DIREWOLF_AUTOSTART=$DIREWOLF_AUTOSTART"

echo -e ""
echo -e "${LIGHT_BLUE}Django configuration environment:${NC}"
echo -e "DJANGO_SUPERUSER_USERNAME=$DJANGO_SUPERUSER_USERNAME"
echo -e "DJANGO_SUPERUSER_PASSWORD=$DJANGO_SUPERUSER_PASSWORD"
echo -e "DJANGO_SUPERUSER_EMAIL=$DJANGO_SUPERUSER_EMAIL"
echo -e "DJANGO_LOG_LEVEL=$DJANGO_LOG_LEVEL"

echo -e ""
echo -e "${LIGHT_BLUE}Nginx configuration environment:${NC}"
echo -e "NGINX_AUTOSTART=$NGINX_AUTOSTART"

echo -e ""
echo -e "${LIGHT_BLUE}Nexus backend autostart:${NC}"
echo -e "NEXUS_BACKEND_AUTOSTART=$NEXUS_BACKEND_AUTOSTART"

echo -e ""
echo -e "${LIGHT_BLUE}Nexus configuration environment:${NC}"
echo -e "NEXUS_CONFIG=$NEXUS_CONFIG"
echo -e "NEXUS_PORT=$NEXUS_PORT"
echo -e "NEXUS_ASPECT=$NEXUS_ASPECT"
echo -e "NEXUS_ROLE=$NEXUS_ROLE"
echo -e "NEXUS_LONGPOLL=$NEXUS_LONGPOLL"
echo -e "NEXUS_TIMEOUT=$NEXUS_TIMEOUT"
echo -e "NEXUS_BRIDGE=$NEXUS_BRIDGE"

echo
echo "RNS Interface Status"
echo "------------------------------------------------------------"
sudo rnstatus --config $RNS_CONFIG 2>&1

echo
echo "Nomadnet Configuration"
echo "------------------------------------------------------------"
cat $NOMADNET_CONFIG/config

echo
echo "RNS Configuration"
echo "------------------------------------------------------------"
cat $RNS_CONFIG/config
