#!/bin/bash
# USE the trap if you need to also do manual cleanup after the service is stopped,
#     or need to start multiple services in the one container
# trap "echo TRAPed signal" HUP INT QUIT TERM

# Log reticulum interface status
echo ""
echo "#############################################################"
echo " Startup of Nexus Server [Django]"
echo "#############################################################"
echo ""
echo "-------------------------------------------------------------"
echo " Environment variables set:"
echo "-------------------------------------------------------------"

# Set default container Nexus API Port to exposed port
NEXUS_PORT="${NEXUS_PORT:-$NEXUS_CONTAINER_API_PORT}"

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
cat .reticulum/config

echo ""
echo "-------------------------------------------------------------"
echo " Actual Reticulum interface status:"
echo "-------------------------------------------------------------"
rnstatus

echo "-------------------------------------------------------------"
echo " Nexus Messenger Web App NGINX configuration check and startup"
echo "-------------------------------------------------------------"
sudo nginx -t
sudo systemctl start nginx
sudo systemctl status nginx

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
echo " Nexus Django Server startup"
echo "-------------------------------------------------------------"
# Launch nexus_server2 Server with unbuffered logs (docker takes those logs)
# exec python3 -u /bsb/nexus_server/nexus_server.py ${NEXUS_CONFIG:+--config=$NEXUS_CONFIG} ${NEXUS_PORT:+--port=$NEXUS_PORT} ${NEXUS_ASPECT:+--aspect=$NEXUS_ASPECT} ${NEXUS_ROLE:+--role=$NEXUS_ROLE} ${NEXUS_LONGPOLL:+--longpoll=$NEXUS_LONGPOLL} ${NEXUS_TIMEOUT:+--timeout=$NEXUS_TIMEOUT} ${NEXUS_BRIDGE:+--bridge=$NEXUS_BRIDGE}

cd nexus_django || exit
#exec gunicorn nexus_django.wsgi:application -t 0 -w 3 -k gevent --bind 0.0.0.0:"$NEXUS_PORT"
exec gunicorn nexus_django.wsgi:application --reload --bind 0.0.0.0:"$NEXUS_PORT"
