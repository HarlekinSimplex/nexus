#!/bin/bash
#################################################
# Set end xport color env variables
#
cat $NOMADNET_CONFIG/storage/pages/banner.txt
echo
sudo rnstatus --config $RNS_CONFIG 2>&1
