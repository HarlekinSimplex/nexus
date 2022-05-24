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

echo -e ""
echo -e "${LIGHT_BLUE}-------------------------------------------------------------${NC}"
echo -e "${LIGHT_BLUE}Startup of Nexus Server [Django]${NC}"
echo -e "${LIGHT_BLUE}-------------------------------------------------------------${NC}"

echo -e ""
echo -e "-------------------------------------------------------------"
echo -e "Migrate Database"
echo -e "-------------------------------------------------------------"
# Check if nexus database directory exists
if test -d ".nexus/database"; then
  echo -e "Nexus database directory 'database' ${LIGHT_GREEN}exists${NC}"
else
  mkdir .nexus/database
  echo -e "Nexus database directory 'database' ${YELLOW}created${NC}"
fi
# Check if nexus database exists
if test -f ".nexus/database/nexus.sqlite3"; then
  echo -e "Nexus database 'nexus.sqlite3' ${LIGHT_GREEN}exists${NC}"
else
  echo -e "Nexus database 'nexus.sqlite3' ${YELLOW}does not exist${NC} (empty database will be created)"
fi
# Create database (if not yet there) and apply migrations
cd nexus_django || exit
./manage.py migrate
cd ..

echo -e ""
echo -e "-------------------------------------------------------------"
echo -e "Check that default Django super user exists"
echo -e "-------------------------------------------------------------"
cd nexus_django || exit
if ! ./manage.py createsuperuser --noinput >/dev/null 2>&1 ; then
  echo -e "Django super user ${LIGHT_GREEN}exists${NC}"
else
  echo -e "Django super user with default credentials was created ${LIGHT_GREEN}successfully${NC}"
fi
cd ..

echo -e ""
echo -e "-------------------------------------------------------------"
echo -e "Nexus Django Server startup (exec -> PID 1)"
echo -e "-------------------------------------------------------------"
cd nexus_django || exit
exec gunicorn nexus_django.wsgi:application \
 --config gunicorn.config.py \
 --log-level "$DJANGO_LOG_LEVEL" \
 --bind 127.0.0.1:"$NEXUS_PORT"
