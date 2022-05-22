#!/bin/bash

if [ "$DIREWOLF_AUTOSTART" != "False" ] ; then
  echo -e ""
  echo -e "-------------------------------------------------------------"
  echo -e "Autostart Direwolf"
  echo -e "-------------------------------------------------------------"
  direwolf -t 0 -c "$DIREWOLF_CONFIG"/direwolf.conf &
  echo "direwolf PID=""$(pgrep direwolf)"
fi

if [ "$SOUNDMODEM_AUTOSTART" != "False" ] ; then
  echo -e ""
  echo -e "-------------------------------------------------------------"
  echo -e "Autostart Soundmodem"
  echo -e "-------------------------------------------------------------"
  sudo soundmodem "$SOUNDMODEM_CONFIG"/soundmodem.conf &
  echo "soundmodem PID=""$(pgrep soundmodem)"
fi

echo -e ""
echo -e "-------------------------------------------------------------"
echo -e "Actual Reticulum interface configuration:"
echo -e "-------------------------------------------------------------"
# Log reticulum interface configuration
cat "$RNS_CONFIG"/config

echo -e ""
echo -e "-------------------------------------------------------------"
echo -e "Actual RNS interface status"
echo -e "-------------------------------------------------------------"
rnstatus

if [ "$RNS_AUTOSTART" != "False" ] ; then
  echo -e ""
  echo -e "-------------------------------------------------------------"
  echo -e "Autostart RNS as service"
  echo -e "-------------------------------------------------------------"
  # Log reticulum interface status
  rnsd -s &
  sleep 1
  echo "RNS PID="$(pgrep rnsd)
fi

if [ "$NOMADNET_AUTOSTART" != "False" ] ; then
  echo -e ""
  echo -e "-------------------------------------------------------------"
  echo -e "Autostart Nomadnetwork as service"
  echo -e "-------------------------------------------------------------"
  # Log reticulum interface status
  nomadnet --daemon &
  sleep 1
  echo "nomadnet PID="$(pgrep nomadnet)
fi

echo -e ""
echo -e "-------------------------------------------------------------"
echo -e "Nexus Messenger Web App NGINX configuration check and startup"
echo -e "-------------------------------------------------------------"
# Log nginx status
sudo nginx -t
sudo systemctl start nginx
sudo systemctl status nginx
