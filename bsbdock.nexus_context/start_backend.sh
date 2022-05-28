#!/bin/bash

# Check if we shall config audio for direwolf and start it
if [ "$DIREWOLF_AUTOSTART" != "False" ] ; then
  echo -e ""
  echo -e "-------------------------------------------------------------"
  echo -e "Autostart Direwolf"
  echo -e "-------------------------------------------------------------"
  if [ -f "$DIREWOLF_CONFIG"/"$DIREWOLF_INTERFACE_NAME".sh ] ; then
    chmod +x "$DIREWOLF_CONFIG"/"$DIREWOLF_INTERFACE_NAME".sh
    "$DIREWOLF_CONFIG"/"$DIREWOLF_INTERFACE_NAME".sh
  else
    echo -e "Direwolf sound setup script file $DIREWOLF_CONFIG/$DIREWOLF_INTERFACE_NAME.sh is ${YELLOW}missing${NC}"
  fi
  echo -e ""
  echo -e "${LIGHT_BLUE}Start direwolf:${NC}"
  echo -e "Using configuration from ${LIGHT_GREEN}$DIREWOLF_CONFIG/$DIREWOLF_INTERFACE_NAME.conf${NC}"
  su bsb -c "direwolf -t 0 -p \
    -c $DIREWOLF_CONFIG/$DIREWOLF_INTERFACE_NAME.conf \
    -l $DIREWOLF_CONFIG/log \
    $DIREWOLF_OPTIONS &"
  sleep 1
  echo "direwolf PID=""$(pgrep direwolf)"
fi

# Check if we shall config audio for soundmodem and start it
if [ "$SOUNDMODEM_AUTOSTART" != "False" ] ; then
  echo -e ""
  echo -e "-------------------------------------------------------------"
  echo -e "Autostart Soundmodem"
  echo -e "-------------------------------------------------------------"
  if [ -f "$SOUNDMODEM_CONFIG"/soundmodem-sound.sh ] ; then
    chmod +x "$SOUNDMODEM_CONFIG"/soundmodem-sound.sh
    "$SOUNDMODEM_CONFIG"/soundmodem-sound.sh
  else
    echo -e "Soundmodem sound setup script file $SOUNDMODEM_CONFIG/soundmodem-sound.sh is ${YELLOW}missing${NC}"
  fi
  echo -e ""
  echo -e "${LIGHT_BLUE}Start soundmodem:${NC}"
  echo -e "Using configuration from ${LIGHT_GREEN}$SOUNDMODEM_CONFIG/soundmodem.conf${NC}"
  su root -c "soundmodem -v 2 $SOUNDMODEM_CONFIG/soundmodem.conf &> $SOUNDMODEM_CONFIG/soundmodem.log &"
  sleep 1
  chmod a+rw /dev/soundmodem0
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
  echo -e "Reticulum config file $RNS_CONFIG/config is ${YELLOW}missing${NC}"
  echo -e "First RNS startup will create and use a default config file"
fi

# Check if we shall RNS explicitly as service
if [ "$RNS_AUTOSTART" != "False" ] ; then
  echo -e ""
  echo -e "-------------------------------------------------------------"
  echo -e "Autostart RNS as service"
  echo -e "-------------------------------------------------------------"
  # Log reticulum interface status
  su bsb -c "rnsd -s --config $RNS_CONFIG &"
  sleep 1
  echo "RNS PID=$(pgrep rnsd)"
fi

echo -e ""
echo -e "-------------------------------------------------------------"
echo -e "Actual RNS interface status"
echo -e "-------------------------------------------------------------"
su bsb -c "rnstatus --config $RNS_CONFIG"

# Check if we shall start nomadnet as headless daemon (for serving pages or as LXMF propagation node)
if [ "$NOMADNET_AUTOSTART" != "False" ] ; then
  echo -e ""
  echo -e "-------------------------------------------------------------"
  echo -e "Autostart Nomadnetwork as service"
  echo -e "-------------------------------------------------------------"
  # Log reticulum interface status
  su bsb -c "nomadnet --daemon --rnsconfig $RNS_CONFIG --config $NOMADNET_CONFIG &"
  sleep 1
  echo "nomadnet PID=$(pgrep nomadnet)"
fi

echo -e ""
echo -e "-------------------------------------------------------------"
echo -e "Nexus Messenger Web App NGINX configuration check and startup"
echo -e "-------------------------------------------------------------"
# Log nginx status
nginx -t
systemctl start nginx
systemctl status nginx
