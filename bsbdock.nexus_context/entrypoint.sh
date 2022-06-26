#!/bin/bash
# Exit on error
set -e

# Set color tags for use with 'echo -e'
export RED='\033[0;31m'
export LIGHT_RED='\033[1;31m'
export GREEN='\033[0;32m'
export LIGHT_GREEN='\033[1;32m'
export YELLOW='\033[0;33m'
export LIGHT_YELLOW='\033[1;33m'
export BLUE='\033[0;34m'
export LIGHT_BLUE='\033[1;34m'
export PURPLE='\033[0;35m'
export LIGHT_PURPLE='\033[1;35m'
export CYAN='\033[0;36m'
export LIGHT_CYAN='\033[1;36m'
export NC='\033[0m' # No Color

echo ' _         _         _            _         __                        '
echo '| |       | |       | |          | |       / /                        '
echo '| |__  ___| |__   __| | ___   ___| | __   / / __   _____  ___   _ ___ '
echo '| '\''_ \/ __| '\''_ \ / _'\`' |/ _ \ / __| |/ /  / / '\''_ \ / _ \ \/ / | | / __|'
echo "| |_) \\__ \\ |_) | (_| | (_) | (__|   <  / /| | | |  __/>  <| |_| \\__ \\"
echo '|_ __/|___/_ __/ \__,_|\___/ \___|_|\_\/_/ |_| |_|\___/_/\_\\__,_|___/'
echo ""
echo "Copyright (c) 2022 Stephan Becker / Becker-Systemberatung, MIT License"

# Define home directory
export HOME=/home/bsb

# Set Reticulum default environment variables
export RNS_CONFIG="${RNS_CONFIG:-$HOME/.reticulum}"
export RNS_AUTOSTART="${RNS_AUTOSTART:-False}"

# Set Nomadnet default environment variables
export NOMADNET_CONFIG="${NOMADNET_CONFIG:-$HOME/.nomadnetwork}"
export NOMADNET_AUTOSTART="${NOMADNET_AUTOSTART:-False}"

# Set Direwolf default environment variables
export DIREWOLF_AUTOSTART="${DIREWOLF_AUTOSTART:-False}"
export DIREWOLF_INSTANCES="${DIREWOLF_INSTANCES:-internal_1}"
export DIREWOLF_CONFIG="${DIREWOLF_CONFIG:-$HOME/.direwolf}"
export DIREWOLF_OPTIONS="${DIREWOLF_OPTIONS:--t 0 -q dx -T %T}"

# Set default super user credentials for django
export DJANGO_SUPERUSER_USERNAME="${DJANGO_SUPERUSER_USERNAME:-admin}"
export DJANGO_SUPERUSER_PASSWORD="${DJANGO_SUPERUSER_PASSWORD:-admin}"
export DJANGO_SUPERUSER_EMAIL="${DJANGO_SUPERUSER_EMAIL:-admin@example.com}"
export DJANGO_LOG_LEVEL="${DJANGO_LOG_LEVEL:-info}"

# Set Nginx default environment variables
export NGINX_AUTOSTART="${NGINX_AUTOSTART:-False}"

# Set Nexus Backend autostart (Switch to backend autostart script)
export NEXUS_BACKEND_AUTOSTART="${NEXUS_BACKEND_AUTOSTART:-True}"

# Set Nexus default environment variables
export NEXUS_CONFIG="${NEXUS_CONFIG:-$HOME/.nexus}"
export NEXUS_PORT="${NEXUS_PORT:-$NEXUS_CONTAINER_API_PORT}"
export NEXUS_ASPECT="${NEXUS_ASPECT:-home}"
export NEXUS_ROLE="${NEXUS_ROLE:-{\"cluster\":\"home\"\}}"
export NEXUS_LONGPOLL="${NEXUS_LONGPOLL:-17280}"
export NEXUS_TIMEOUT="${NEXUS_TIMEOUT:-43200}"
export NEXUS_BRIDGE="${NEXUS_BRIDGE:-[]}"

echo ""
echo "-------------------------------------------------------------"
echo "Change uid and gid of node user so it matches ownership of current dir"
echo "-------------------------------------------------------------"
cd "$HOME"
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

echo -e ""
echo -e "-------------------------------------------------------------"
echo -e "Environment variables set:"
echo -e "-------------------------------------------------------------"

echo -e "${LIGHT_BLUE}Reticulum configuration environment:${NC}"
echo -e "RNS_CONFIG=$RNS_CONFIG"
echo -e "RNS_AUTOSTART=$RNS_AUTOSTART"

echo -e ""
echo -e "${LIGHT_BLUE}Nomadnetwork configuration environment:${NC}"
echo -e "NOMADNET_CONFIG=$NOMADNET_CONFIG"
echo -e "NOMADNET_AUTOSTART=$NOMADNET_AUTOSTART"

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

echo -e ""
echo -e "-------------------------------------------------------------"
echo -e "Check configuration environment:"
echo -e "-------------------------------------------------------------"

# Check if direwolf config directory exists
if [ -d "$DIREWOLF_CONFIG" ] ; then
  echo -e "Direwolf config directory '$DIREWOLF_CONFIG' ${LIGHT_GREEN}exists${NC}"
else
  mkdir "$DIREWOLF_CONFIG"
  echo -e "Direwolf config directory '$DIREWOLF_CONFIG' ${YELLOW}created${NC}"
fi
chown bsb:bsb -R "$DIREWOLF_CONFIG"
chmod -R 755 "$DIREWOLF_CONFIG"

# Check if reticulum config directory exists
if [ -d "$RNS_CONFIG" ] ; then
  echo -e "Reticulum config directory '$RNS_CONFIG' ${LIGHT_GREEN}exists${NC}"
else
  mkdir "$RNS_CONFIG"
  echo -e "Reticulum config directory '$RNS_CONFIG' ${YELLOW}created${NC}"
fi
if [ -f "$RNS_CONFIG/logfile" ] ; then
  rm "$RNS_CONFIG/logfile"
  echo "RNS restart on $(date)" >"$RNS_CONFIG/logfile"
fi
chown bsb:bsb -R "$RNS_CONFIG"
chmod -R 755 "$RNS_CONFIG"

# Check if nomadnetwork config directory exists
if [ -d "$NOMADNET_CONFIG" ] ; then
  echo -e "Nomadnetwork config directory '$NOMADNET_CONFIG' ${LIGHT_GREEN}exists${NC}"
else
  mkdir "$NOMADNET_CONFIG"
  echo -e "Nomadnetwork config directory '$NOMADNET_CONFIG' ${YELLOW}created${NC}"
fi
if [ -f "$NOMADNET_CONFIG/logfile" ] ; then
  rm "$NOMADNET_CONFIG/logfile"
  echo "Nomadnet restart on $(date)" >"$NOMADNET_CONFIG/logfile"
fi
chown bsb:bsb -R "$NOMADNET_CONFIG"
chmod -R 755 "$NOMADNET_CONFIG"

# Check if nexus config directory exists
if [ -d "$NEXUS_CONFIG" ] ; then
  echo -e "Nexus config directory '$NEXUS_CONFIG' ${LIGHT_GREEN}exists${NC}"
else
  mkdir "$NEXUS_CONFIG"
  echo -e "Nexus config directory '$NEXUS_CONFIG' ${YELLOW}created${NC}"
fi
chown bsb:bsb -R "$NEXUS_CONFIG"
chmod -R 755 "$NEXUS_CONFIG"

# Check if nexus config directory exists
if [ "$NEXUS_BACKEND_AUTOSTART" != "False" ] ; then
  echo -e ""
  echo -e "${LIGHT_BLUE}-------------------------------------------------------------${NC}"
  echo -e "${LIGHT_BLUE}Startup server backend${NC}"
  echo -e "${LIGHT_BLUE}-------------------------------------------------------------${NC}"

  # Initialize server backend
  source start_backend.sh
fi

# Check if rns should be started as command
# If so run it as root
if [ "$1" == "rnsd" ] ; then
  echo ""
  echo "-------------------------------------------------------------"
  echo "Set command to Nomadnetwork client with gui"
  rnsd --version
  set -- rnsd --verbose --config "$RNS_CONFIG"
  # shellcheck disable=SC2145
  echo "Run start command: '$@'"
  echo "... using GOSU with user root"
  echo "-------------------------------------------------------------"
  exec gosu root "$@"
fi

# Check if nomadnet should be started as daemon
# if so run it headless daemon
if [ "$1" == "nomadnet_daemon" ] ; then
  echo ""
  echo "-------------------------------------------------------------"
  echo "Set command to Nomadnetwork client as headless demon"
  nomadnet --version
#  set -- nomadnet --daemon --console --rnsconfig "$RNS_CONFIG" --config "$NOMADNET_CONFIG" 2>&1
  set -- nomadnet -d --rnsconfig "$RNS_CONFIG" --config "$NOMADNET_CONFIG"

# otherwise run it as normal with gui
elif [ "$1" == "nomadnet" ] ; then
  echo ""
  echo "-------------------------------------------------------------"
  echo "Set command to Nomadnetwork client with gui"
  nomadnet --version
  set -- nomadnet --rnsconfig "$RNS_CONFIG" --config "$NOMADNET_CONFIG"
fi

# shellcheck disable=SC2145
echo "Run start command: '$@'"
echo "... using GOSU with user bsb"
echo "-------------------------------------------------------------"
exec gosu bsb "$@"
