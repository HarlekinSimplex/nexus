#!/bin/bash
# USE the trap if you need to also do manual cleanup after the service is stopped,
#     or need to start multiple services in the one container
# trap "echo TRAPed signal" HUP INT QUIT TERM

export RED='\033[0;31m'
export YELLOW='\033[1;33m'
export GREEN='\033[0;32m'
export BLUE='\033[0;34m'
export CYAN='\033[0;36m'
export NC='\033[0m' # No Color

# Log reticulum interface status
echo ""
echo "#############################################################"
echo " Startup of Nexus Server [Django]"
echo "#############################################################"

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
echo " Nexus environment variables set:"
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
echo " Default Django environment variables set:"
echo "-------------------------------------------------------------"
echo "DJANGO_SUPERUSER_USERNAME=$DJANGO_SUPERUSER_USERNAME"
echo "DJANGO_SUPERUSER_PASSWORD=$DJANGO_SUPERUSER_PASSWORD"
echo "DJANGO_SUPERUSER_EMAIL=$DJANGO_SUPERUSER_EMAIL"
echo "DJANGO_LOG_LEVEL=$DJANGO_LOG_LEVEL"

echo ""
echo "-------------------------------------------------------------"
echo " Migrate Database"
echo "-------------------------------------------------------------"
if test -f ".nexus"; then
  echo -e "${GREEN}Nexus config directory '.nexus' exists.${NC}"
else
  mkdir .nexus
  echo -e "${YELLOW}Nexus config directory '.nexus' created.${NC}"
fi
if test -f "database"; then
  echo -e "${GREEN}Nexus database directory 'database' exists.${NC}"
else
  mkdir .nexus/database
  echo -e "${YELLOW}Nexus database directory 'database' created.${NC}"
fi
cd nexus_django || exit
./manage.py migrate
cd ..

#echo ""
#echo "-------------------------------------------------------------"
#echo " Create default Django Super User"
#echo "-------------------------------------------------------------"
#cd nexus_django || exit
#if ! ./manage.py createsuperuser --noinput >/dev/null 2>&1 ; then
#    echo "Super User already exists and cannot be replaced"
#else
#    echo "Default Super User successfully created"
#fi
#cd ..

echo ""
echo "-------------------------------------------------------------"
echo " Nexus Django Server startup"
echo "-------------------------------------------------------------"
cd nexus_django || exit
exec gunicorn --config gunicorn.config.py --bind 127.0.0.1:"$NEXUS_PORT" nexus_django.wsgi:application
