#!/bin/bash
# Log reticulum interface status
echo "#############################################################"
echo "# Welcome to bsbdock/nexus                                  #"
echo "# A broadcast messaging server based on Reticulum           #"
echo "#############################################################"

echo ""
echo "-------------------------------------------------------------"
echo " Environment variables set:"
echo "-------------------------------------------------------------"
echo "NEXUS_CONFIG=$NEXUS_CONFIG"
echo "NEXUS_PORT=$NEXUS_PORT"
echo "NEXUS_ASPECT=$NEXUS_ASPECT"
echo "NEXUS_ROLE=$NEXUS_ROLE"
echo "NEXUS_LONGPOLL=$NEXUS_LONGPOLL"
echo "NEXUS_TIMEOUT=$NEXUS_TIMEOUT"
echo "NEXUS_BRIDGE=$NEXUS_BRIDGE"

echo ""
echo "-------------------------------------------------------------"
echo " Actual Reticulum interface configuration:"
echo "-------------------------------------------------------------"
cat /root/.reticulum/config

echo ""
echo "-------------------------------------------------------------"
echo " Actual Reticulum interface status:"
echo "-------------------------------------------------------------"
rnstatus

echo "-------------------------------------------------------------"
echo " Nexus Messenger Web App NGINX configuration check and startup"
echo "-------------------------------------------------------------"
nginx -t
systemctl start nginx
systemctl status nginx

echo ""
echo "-------------------------------------------------------------"
echo " Django server startup"
echo "-------------------------------------------------------------"
python /bsb/nexus_django/manage.py runserver &

#echo ""
#echo "-------------------------------------------------------------"
#echo " Direwolf startup"
#echo "-------------------------------------------------------------"
#direwolf -t 0

echo ""
echo "-------------------------------------------------------------"
echo " Parameters passed to server startup:"
echo "-------------------------------------------------------------"
echo \
${NEXUS_CONFIG:+--config=$NEXUS_CONFIG} \
${NEXUS_PORT:+--port=$NEXUS_PORT} \
${NEXUS_ASPECT:+--aspect=$NEXUS_ASPECT} \
${NEXUS_ROLE:+--role=$NEXUS_ROLE} \
${NEXUS_LONGPOLL:+--longpoll=$NEXUS_LONGPOLL} \
${NEXUS_TIMEOUT:+--timeout=$NEXUS_TIMEOUT} \
${NEXUS_BRIDGE:+--bridge=$NEXUS_BRIDGE}

echo ""
echo "-------------------------------------------------------------"
echo " Nexus Server startup"
echo "-------------------------------------------------------------"
# Launch nexus_server2 Server with unbuffered logs (docker takes those logs)
python3 -u /bsb/nexus_server/nexus_server.py ${NEXUS_CONFIG:+--config=$NEXUS_CONFIG} ${NEXUS_PORT:+--port=$NEXUS_PORT} ${NEXUS_ASPECT:+--aspect=$NEXUS_ASPECT} ${NEXUS_ROLE:+--role=$NEXUS_ROLE} ${NEXUS_LONGPOLL:+--longpoll=$NEXUS_LONGPOLL} ${NEXUS_TIMEOUT:+--timeout=$NEXUS_TIMEOUT} ${NEXUS_BRIDGE:+--bridge=$NEXUS_BRIDGE}

echo ""
echo "-------------------------------------------------------------"
echo " Nexus Server terminated"
echo "-------------------------------------------------------------"

exit