#!/bin/bash
###############################################################################
# Audio setup script for 'USB Audio CODEC' type devices
#

# Set sound card default
export DIREWOLF_SOUND_CARD="${DIREWOLF_SOUND_CARD:-1}"
# Check if we have a dual device configuration set up
# Default is 'No'
export DIREWOLF_DUAL_SOUND_CARD="${DIREWOLF_DUAL_SOUND_CARD:-No}"
# Set dual device config defaults
export DIREWOLF_INPUT_SOUND_CARD="${DIREWOLF_INPUT_SOUND_CARD:-$DIREWOLF_SOUND_CARD}"
export DIREWOLF_OUTPUT_SOUND_CARD="${DIREWOLF_OUTPUT_SOUND_CARD:-$DIREWOLF_SOUND_CARD}"

# Set Output defaults for USB AUdio CODEC
export DIREWOLF_PCM_PLAYBACK_SWITCH="${DIREWOLF_PCM_PLAYBACK_SWITCH:-on}"
export DIREWOLF_PCM_PLAYBACK_VOLUME="${DIREWOLF_PCM_PLAYBACK_VOLUME:-80%}"
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
echo -e "${LIGHT_BLUE}ALSA sound device selection:${NC}"
echo -e "DIREWOLF_SOUND_CARD=$DIREWOLF_SOUND_CARD"
echo -e ""
echo -e "${LIGHT_BLUE}Sound output channel parameters:${NC}"
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
amixer -c "$DIREWOLF_SOUND_CARD" cset name='PCM Playback Switch' "DIREWOLF_PCM_PLAYBACK_SWITCH"
amixer -c "$DIREWOLF_SOUND_CARD" cset name='PCM Playback Volume' "DIREWOLF_PCM_PLAYBACK_VOLUME"

# Log all controls for selected sound card spec
echo -e ""
echo -e "${LIGHT_BLUE}Actual contents set for input/output card $DIREWOLF_SOUND_CARD:${NC}"
amixer -c "$DIREWOLF_SOUND_CARD" contents
