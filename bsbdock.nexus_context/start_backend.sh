#!/bin/bash

if [ "$DIREWOLF_AUTOSTART" != "False" ] ; then
  echo -e ""
  echo -e "-------------------------------------------------------------"
  echo -e "Autostart Direwolf"
  echo -e "-------------------------------------------------------------"
  direwolf -t 0 -c "$DIREWOLF_CONFIG"/direwolf.conf &
  sleep 1
  echo "direwolf PID=""$(pgrep direwolf)"
fi

if [ "$SOUNDMODEM_AUTOSTART" != "False" ] ; then
  echo -e ""
  echo -e "-------------------------------------------------------------"
  echo -e "Autostart Soundmodem"
  echo -e "-------------------------------------------------------------"
  soundmodem "$SOUNDMODEM_CONFIG"/soundmodem.conf &
  sleep 1
  echo "soundmodem PID=""$(pgrep soundmodem)"
fi

echo -e ""
echo -e "-------------------------------------------------------------"
echo -e "Actual Reticulum interface configuration:"
echo -e "-------------------------------------------------------------"
# Log reticulum interface configuration
if [ -f "$RNS_CONFIG"/config ] ; then
  cat "$RNS_CONFIG"/config
else
  echo -e "Reticulum config file "$RNS_CONFIG"/config is ${YELLOW}missing${NC}"
  echo -e "First RNS startup will create and use a default config file"
fi

echo -e ""
echo -e "-------------------------------------------------------------"
echo -e "Actual RNS interface status"
echo -e "-------------------------------------------------------------"
rnstatus --config "$RNS_CONFIG"

if [ "$RNS_AUTOSTART" != "False" ] ; then
  echo -e ""
  echo -e "-------------------------------------------------------------"
  echo -e "Autostart RNS as service"
  echo -e "-------------------------------------------------------------"
  # Log reticulum interface status
  rnsd -s --config "$RNS_CONFIG" &
  sleep 1
  echo "RNS PID="$(pgrep rnsd)
fi

if [ "$NOMADNET_AUTOSTART" != "False" ] ; then
  echo -e ""
  echo -e "-------------------------------------------------------------"
  echo -e "Autostart Nomadnetwork as service"
  echo -e "-------------------------------------------------------------"
  # Log reticulum interface status
  nomadnet --daemon --rnsconfig "$RNS_CONFIG" --config "$NOMADNET_CONFIG" &
  sleep 1
  echo "nomadnet PID="$(pgrep nomadnet)
fi

echo -e ""
echo -e "-------------------------------------------------------------"
echo -e "Nexus Messenger Web App NGINX configuration check and startup"
echo -e "-------------------------------------------------------------"
# Log nginx status
nginx -t
systemctl start nginx
systemctl status nginx
