#!/bin/bash
# Log reticulum interface status
rnstatus

# Launch Nexus Server with unbuffered logs (docker takes those logs)
python3 -u /bsb/Nexus/NexusServer.py
