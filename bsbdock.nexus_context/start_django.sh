#!/bin/bash
# USE the trap if you need to also do manual cleanup after the service is stopped,
#   or need to start multiple services in the one container
# trap "echo TRAPed signal" HUP INT QUIT TERM

# Exit on error
set -e

# Set color tags for use with 'echo -e'
export RED='\033[0;31m'
export LIGHT_RED='\033[1;31m'
export YELLOW='\033[1;33m'
export GREEN='\033[0;32m'
export LIGHT_GREEN='\033[1;32m'
export BLUE='\033[0;34m'
export LIGHT_BLUE='\033[1;34m'
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
# Check if nexus config directory exists
if test -d ".nexus"; then
  echo -e "Nexus config directory '.nexus' ${LIGHT_GREEN}exists${NC}"
else
  mkdir .nexus
  echo -e "Nexus config directory '.nexus' ${YELLOW}created${NC}"
fi
# Check if nexus database directory exists
if test -d ".nexus/database"; then
  echo -e "Nexus database directory 'database' ${LIGHT_GREEN}exists${NC}"
else
  mkdir .nexus/database
  echo -e "Nexus database directory 'database' ${YELLOW}created${NC}"
fi
# Check if nexus database exists (info onöy)
if test -f ".nexus/database/nexus.sqlite3"; then
  echo -e "Nexus database 'nexus.sqlite3' ${LIGHT_GREEN}exists${NC}"
else
  echo -e "Nexus database 'nexus.sqlite3' ${YELLOW}does not exist${NC} (empty database will be created)"
fi
# Create database (if not yet there) and apply migrations
cd nexus_django || exit
./manage.py migrate
cd ..

echo ""
echo "-------------------------------------------------------------"
echo " Check that default Django super user exists"
echo "-------------------------------------------------------------"
cd nexus_django || exit
if ! ./manage.py createsuperuser --noinput >/dev/null 2>&1 ; then
    echo -e "Django super user ${LIGHT_GREEN}exists${NC}"
else
    echo -e "Django super user with default credentials was created ${LIGHT_GREEN}successfully${NC}"
fi
cd ..

echo ""
echo "-------------------------------------------------------------"
echo " Nexus Django Server startup"
echo "-------------------------------------------------------------"
cd nexus_django || exit
exec gunicorn nexus_django.wsgi:application \
 --config gunicorn.config.py \
 --log-level "$DJANGO_LOG_LEVEL" \
 --bind 127.0.0.1:"$NEXUS_PORT"
