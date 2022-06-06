#!/bin/bash

# Check if we shall config audio for direwolf and start it
if [ "$DIREWOLF_AUTOSTART" != "False" ] ; then
  echo -e ""
  echo -e "-------------------------------------------------------------"
  echo -e "Autostart Direwolf"
  echo -e "-------------------------------------------------------------"
  # Startup dw instances
  for DW_INST in $DIREWOLF_INSTANCES
  do
    echo -e ""
    echo -e "-------------------------------------------------------------"
    echo -e "${LIGHT_BLUE}Configure sound devices for direwolf instance $DW_INST:${NC}"
    echo -e "-------------------------------------------------------------"
  # Check for device script file
    if [ -f "$DIREWOLF_CONFIG/$DW_INST.sh" ] ; then
      # Make sound set up script executable for this container user (root)
      chmod +x "$DIREWOLF_CONFIG/$DW_INST.sh"
      "$DIREWOLF_CONFIG/$DW_INST.sh" "$DW_INST"
    else
      echo -e "Direwolf sound setup script file $DIREWOLF_CONFIG/$DW_INST.sh is ${YELLOW}missing${NC}"
      break
    fi
    # Check for dw config file
    if [ -f "$DIREWOLF_CONFIG/$DW_INST.conf" ] ; then
      echo -e ""
      echo -e "-------------------------------------------------------------"
      echo -e "${LIGHT_BLUE}Start direwolf instance $DW_INST:${NC}"
      echo -e "-------------------------------------------------------------"
      echo -e "Using configuration from ${LIGHT_GREEN}$DIREWOLF_CONFIG/$DW_INST.conf${NC}"
      # Make GPIO pins accessible for any user and any group
      # Group gpio does not exists on OrangePI!
      chmod ug+w /sys/class/gpio/export
      # Launch direwolf
      su bsb -c "direwolf $DIREWOLF_OPTIONS -c $DIREWOLF_CONFIG/$DW_INST.conf -l $DIREWOLF_CONFIG/log &"
      sleep 1
    else
      echo -e "Direwolf sound setup script file $DIREWOLF_CONFIG/$DW_INST.sh is ${YELLOW}missing${NC}"
      break
    fi
  # Loop through specified config ID's
  done
  echo -e "-------------------------------------------------------------"
  printf "direwolf PID's in use:\n"
  pgrep direwolf
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
sleep 2
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
