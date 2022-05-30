#!/bin/bash
###############################################################################
# Audio setup script for 'USB Audio CODEC' type devices
#
# $1 contains the naked dw instance name as specified by the .env or entrypoint.sh
# It is used to pull in defaults to be used for this usb sound board

# Use these environment variables in .env to setup device parameters for this backend startup script
#DIREWOLF_INTERFACE_NAME=<Interface Name>
#
# Direwolf default interface device configuration
#DIREWOLF_<dw-instance>_SOUND_CARD=1
#
# Direwolf default amixer content values
#DIREWOLF_<dw-instance>_PCM_PLAYBACK_SWITCH=on
#DIREWOLF_<dw-instance>_PCM_PLAYBACK_VOLUME=80%

# Set sound card default
DIREWOLF_SOUND_CARD="${DIREWOLF_$1_SOUND_CARD:-1}"

# Set Output defaults for USB AUdio CODEC
DIREWOLF_PCM_PLAYBACK_SWITCH="${DIREWOLF_$1_PCM_PLAYBACK_SWITCH:-on}"
DIREWOLF_PCM_PLAYBACK_VOLUME="${DIREWOLF_$1_PCM_PLAYBACK_VOLUME:-80%}"
# Set Output defaults
# - Intentionally left blank -

# Log all sound cards available
echo -e ""
echo -e "${LIGHT_BLUE}Input cards available:${NC}"
arecord -l
echo -e ""
echo -e "${LIGHT_BLUE}Output cards available:${NC}"
aplay -l

# Set some defaults
echo -e ""
echo -e "${LIGHT_BLUE}ALSA sound device selection for direwolf instance $1:${NC}"
echo -e "DIREWOLF_SOUND_CARD=$DIREWOLF_SOUND_CARD"
echo -e ""
echo -e "${LIGHT_BLUE}Sound output channel parameters for direwolf instance $1:${NC}"
echo -e "DIREWOLF_PCM_PLAYBACK_SWITCH=$DIREWOLF_PCM_PLAYBACK_SWITCH"
echo -e "DIREWOLF_PCM_PLAYBACK_VOLUME=$DIREWOLF_PCM_PLAYBACK_VOLUME"

# Log all controls for selected sound card spec
# Set Card ID for single device setup
echo -e ""
echo -e "${LIGHT_BLUE}Available controls for input/output card $DIREWOLF_SOUND_CARD:${NC}"
amixer -c "$DIREWOLF_SOUND_CARD" controls

# Set mixer configuration as defined
echo -e ""
echo -e "${LIGHT_BLUE}Set output parameters:${NC}"
amixer -c "$DIREWOLF_SOUND_CARD" cset name='PCM Playback Switch' "$DIREWOLF_PCM_PLAYBACK_SWITCH"
amixer -c "$DIREWOLF_SOUND_CARD" cset name='PCM Playback Volume' "$DIREWOLF_PCM_PLAYBACK_VOLUME"

# Log all controls for selected sound card spec
echo -e ""
echo -e "${LIGHT_BLUE}Actual contents set for input/output card $DIREWOLF_SOUND_CARD:${NC}"
amixer -c "$DIREWOLF_SOUND_CARD" contents
