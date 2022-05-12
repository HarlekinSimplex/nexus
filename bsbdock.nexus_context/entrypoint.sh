#!/bin/bash
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

echo ' _         _         _            _         __                        '
echo '| |       | |       | |          | |       / /                        '
echo '| |__  ___| |__   __| | ___   ___| | __   / / __   _____  ___   _ ___ '
echo '| '\''_ \/ __| '\''_ \ / _'\`' |/ _ \ / __| |/ /  / / '\''_ \ / _ \ \/ / | | / __|'
echo "| |_) \\__ \\ |_) | (_| | (_) | (__|   <  / /| | | |  __/>  <| |_| \\__ \\"
echo '|_ __/|___/_ __/ \__,_|\___/ \___|_|\_\/_/ |_| |_|\___/_/\_\\__,_|___/'
echo ""
echo "Copyright (c) 2022 Stephan Becker / Becker-Systemberatung, MIT License"

echo ""
echo "-------------------------------------------------------------"
echo "Check configuration directories"
echo "-------------------------------------------------------------"
# Define home directory
HOME=/home/bsb

# Check if nexus config directory exists
if [ -d "$HOME"/.nexus ] ; then
  echo -e "Nexus config directory '.nexus' ${LIGHT_GREEN}exists${NC}"
else
  mkdir "$HOME"/.nexus
  echo -e "Nexus config directory '.nexus' ${YELLOW}created${NC}"
fi
chown bsb:bsb -R "$HOME"/.nexus
chmod -R 755 "$HOME"/.nexus

# Check if reticulum config directory exists
if [ -d "$HOME"/.reticulum ] ; then
  echo -e "Reticulum config directory '.reticulum' ${LIGHT_GREEN}exists${NC}"
else
  mkdir "$HOME"/.reticulum
  echo -e "Reticulum config directory '.reticulum' ${YELLOW}created${NC}"
fi
chown bsb:bsb -R "$HOME"/.reticulum
chmod -R 755 "$HOME"/.reticulum

# Check if reticulum config directory exists
if [ -d "$HOME"/.nomadnetwork ] ; then
  echo -e "Nomadnetwork config directory '.nomadnetwork' ${LIGHT_GREEN}exists${NC}"
else
  mkdir "$HOME"/.nomadnetwork
  echo -e "Nomadnetwork config directory '.nomadnetwork' ${YELLOW}created${NC}"
fi
chown bsb:bsb -R "$HOME"/.nomadnetwork
chmod -R 755 "$HOME"/.nomadnetwork

# Set Nexus Default environment variables
export NEXUS_PORT="${NEXUS_PORT:-$NEXUS_CONTAINER_API_PORT}"
export NEXUS_ASPECT="${NEXUS_ASPECT:-home}"
export NEXUS_ROLE="${NEXUS_ROLE:-{\"cluster\":\"home\"}"
export NEXUS_LONGPOLL="${NEXUS_LONGPOLL:-17280}"
export NEXUS_TIMEOUT="${NEXUS_TIMEOUT:-43200}"
export NEXUS_BRIDGE="${NEXUS_BRIDGE:-[]}"

# Set default super user credentials for django
export DJANGO_SUPERUSER_USERNAME="${DJANGO_SUPERUSER_USERNAME:-admin}"
export DJANGO_SUPERUSER_PASSWORD="${DJANGO_SUPERUSER_PASSWORD:-admin}"
export DJANGO_SUPERUSER_EMAIL="${DJANGO_SUPERUSER_EMAIL:-admin@example.com}"
export DJANGO_LOG_LEVEL="${DJANGO_LOG_LEVEL:-info}"

echo ""
echo "-------------------------------------------------------------"
echo "Switch from user root to user bsb"
echo "-------------------------------------------------------------"
# Change uid and gid of node user so it matches ownership of current dir
if [ "$MAP_NODE_UID" != "no" ]; then
    if [ ! -d "$MAP_NODE_UID" ]; then
        MAP_NODE_UID=$PWD
    fi

    uid=$(stat -c '%u' "$MAP_NODE_UID")
    gid=$(stat -c '%g' "$MAP_NODE_UID")

    echo "bsb ---> UID = $uid / GID = $gid"

    export USER=bsb

    usermod -u "$uid" bsb 2> /dev/null && {
      groupmod -g "$gid" bsb 2> /dev/null || usermod -a -G "$gid" bsb
    }
fi

echo ""
echo "-------------------------------------------------------------"
echo "Run given start command using GOSU with user bsb"
echo "-------------------------------------------------------------"

echo 'gosu bsb "$@"'
exec gosu bsb "$@"
