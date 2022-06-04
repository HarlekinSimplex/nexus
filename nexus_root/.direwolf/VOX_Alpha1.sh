#!/bin/bash
###############################################################################
# Audio setup script for 'USB Audio Device' type devices
# This script can be used for single or dual channel configurations
#
# $1 contains the dw instance name as specified by the .env or entrypoint.sh.
# It is used to pull in specs to be used for this usb sound board from environment variables.
# If these env variables are not defined some reasonable defaults are used.
# The used defaults assume that each USB Device has been assigned custom names Alpha..Delta.
# See folder nexus_setup for instructions how to do that.
# Alternatively standard device naming as indicated by 'aplay -l' can be used as well.

# Use these environment variables in .env to setup device parameters for this backend startup script
#DIREWOLF_INTERFACE_NAME=<Interface Name>
#
# Direwolf default interface device configuration
#DIREWOLF_VOX_ALPHA_1_SOUND_CARD=Alpha
#DIREWOLF_VOX_ALPHA_1_DUAL_SOUND_CARD=No
#DIREWOLF_VOX_ALPHA_1_INPUT_SOUND_CARD=Alpha
#DIREWOLF_VOX_ALPHA_1_OUTPUT_SOUND_CARD=Alpha
#
# Direwolf default amixer content values
#DIREWOLF_VOX_ALPHA_1_MIC_CAPTURE_SWITCH=on
#DIREWOLF_VOX_ALPHA_1_MIC_CAPTURE_VOLUME=80%
#DIREWOLF_VOX_ALPHA_1_AUTO_GAIN_CONTROL=off
#DIREWOLF_VOX_ALPHA_1_MIC_PLAYBACK_SWITCH=off
#DIREWOLF_VOX_ALPHA_1_MIC_PLAYBACK_VOLUME=0%
#DIREWOLF_VOX_ALPHA_1_SPEAKER_PLAYBACK_SWITCH=on
#DIREWOLF_VOX_ALPHA_1_SPEAKER_PLAYBACK_VOLUME=80%

# Uppercase $1 for env variable forming
DW_INST=$(echo "$1" | tr '[:lower:]' '[:upper:]')

# Set sound card default
TMP=DIREWOLF_"$DW_INST"_SOUND_CARD ; DIREWOLF_SOUND_CARD="${!TMP:-Alpha}"
# Check if we have a dual device configuration set up
# Default is 'No'
TMP=DIREWOLF_"$DW_INST"_DUAL_SOUND_CARD ; DIREWOLF_DUAL_SOUND_CARD="${!TMP:-No}"
# Set dual device config defaults
TMP=DIREWOLF_"$DW_INST"_INPUT_SOUND_CARD ; DIREWOLF_INPUT_SOUND_CARD="${!TMP:-$DIREWOLF_SOUND_CARD}"
TMP=DIREWOLF_"$DW_INST"_OUTPUT_SOUND_CARD ; DIREWOLF_OUTPUT_SOUND_CARD="${!TMP:-$DIREWOLF_SOUND_CARD}"
# Set Input defaults
TMP=DIREWOLF_"$DW_INST"_MIC_CAPTURE_SWITCH ; DIREWOLF_MIC_CAPTURE_SWITCH="${!TMP:-on}"
TMP=DIREWOLF_"$DW_INST"_MIC_CAPTURE_VOLUME ; DIREWOLF_MIC_CAPTURE_VOLUME="${!TMP:-80%}"
TMP=DIREWOLF_"$DW_INST"_AUTO_GAIN_CONTROL ; DIREWOLF_AUTO_GAIN_CONTROL="${!TMP:-off}"
TMP=DIREWOLF_"$DW_INST"_MIC_PLAYBACK_SWITCH ; DIREWOLF_MIC_PLAYBACK_SWITCH="${!TMP:-off}"
TMP=DIREWOLF_"$DW_INST"_MIC_PLAYBACK_VOLUME ; DIREWOLF_MIC_PLAYBACK_VOLUME="${!TMP:-0%}"
# Set Output defaults
TMP=DIREWOLF_"$DW_INST"_SPEAKER_PLAYBACK_SWITCH ; DIREWOLF_SPEAKER_PLAYBACK_SWITCH="${!TMP:-on}"
TMP=DIREWOLF_"$DW_INST"_SPEAKER_PLAYBACK_VOLUME ; DIREWOLF_SPEAKER_PLAYBACK_VOLUME="${!TMP:-80%}"

# Set Card ID for single device setup
if [ "$DIREWOLF_DUAL_SOUND_CARD" != "Yes" ] ; then
  DIREWOLF_INPUT_SOUND_CARD=$DIREWOLF_SOUND_CARD
  DIREWOLF_OUTPUT_SOUND_CARD=$DIREWOLF_SOUND_CARD
fi

# Log all sound cards available
echo -e ""
echo -e "${LIGHT_BLUE}Input cards available:${NC}"
arecord -l
echo -e ""
echo -e "${LIGHT_BLUE}Output cards available:${NC}"
aplay -l

# Set some defaults
echo -e ""
echo -e "${LIGHT_BLUE}ALSA sound device selection for direwolf instance $DW_INST:${NC}"
echo -e "DIREWOLF_DUAL_SOUND_CARD=$DIREWOLF_DUAL_SOUND_CARD"
echo -e "DIREWOLF_SOUND_CARD=$DIREWOLF_SOUND_CARD"
echo -e "DIREWOLF_INPUT_SOUND_CARD=$DIREWOLF_INPUT_SOUND_CARD"
echo -e "DIREWOLF_OUTPUT_SOUND_CARD=$DIREWOLF_OUTPUT_SOUND_CARD"
echo -e ""
echo -e "${LIGHT_BLUE}Sound input channel parameters for direwolf instance $DW_INST:${NC}"
echo -e "DIREWOLF_MIC_CAPTURE_SWITCH=$DIREWOLF_MIC_CAPTURE_SWITCH"
echo -e "DIREWOLF_MIC_CAPTURE_VOLUME=$DIREWOLF_MIC_CAPTURE_VOLUME"
echo -e "DIREWOLF_MIC_PLAYBACK_SWITCH=$DIREWOLF_MIC_PLAYBACK_SWITCH"
echo -e "DIREWOLF_MIC_PLAYBACK_VOLUME=$DIREWOLF_MIC_PLAYBACK_VOLUME"
echo -e "DIREWOLF_AUTO_GAIN_CONTROL=$DIREWOLF_AUTO_GAIN_CONTROL"
echo -e ""
echo -e "${LIGHT_BLUE}Sound output channel parameters for direwolf instance $DW_INST:${NC}"
echo -e "DIREWOLF_SPEAKER_PLAYBACK_SWITCH=$DIREWOLF_SPEAKER_PLAYBACK_SWITCH"
echo -e "DIREWOLF_SPEAKER_PLAYBACK_VOLUME=$DIREWOLF_SPEAKER_PLAYBACK_VOLUME"

# Log all controls for selected sound card spec
# Set Card ID for single device setup
if [ "$DIREWOLF_DUAL_SOUND_CARD" == "Yes" ] ; then
  echo -e ""
  echo -e "${LIGHT_BLUE}Available controls for input card $DIREWOLF_INPUT_SOUND_CARD:${NC}"
  amixer -c "$DIREWOLF_INPUT_SOUND_CARD" controls
  echo -e ""
  echo -e "${LIGHT_BLUE}Available controls for output card $DIREWOLF_OUTPUT_SOUND_CARD:${NC}"
  amixer -c "$DIREWOLF_OUTPUT_SOUND_CARD" controls
else
  echo -e ""
  echo -e "${LIGHT_BLUE}Available controls for input/output card $DIREWOLF_SOUND_CARD:${NC}"
  amixer -c "$DIREWOLF_SOUND_CARD" controls
fi

# Set mixer configuration as defined
echo -e ""
echo -e "${LIGHT_BLUE}Set input parameters:${NC}"
amixer -c "$DIREWOLF_INPUT_SOUND_CARD" cset name='Mic Capture Switch' "$DIREWOLF_MIC_CAPTURE_SWITCH"
amixer -c "$DIREWOLF_INPUT_SOUND_CARD" cset name='Mic Capture Volume' "$DIREWOLF_MIC_CAPTURE_VOLUME"
amixer -c "$DIREWOLF_INPUT_SOUND_CARD" cset name='Mic Playback Switch' "$DIREWOLF_MIC_PLAYBACK_SWITCH"
amixer -c "$DIREWOLF_INPUT_SOUND_CARD" cset name='Mic Playback Volume' "$DIREWOLF_MIC_PLAYBACK_VOLUME"
amixer -c "$DIREWOLF_INPUT_SOUND_CARD" cset name='Auto Gain Control' "$DIREWOLF_AUTO_GAIN_CONTROL"

echo -e ""
echo -e "${LIGHT_BLUE}Set output parameters:${NC}"
amixer -c "$DIREWOLF_OUTPUT_SOUND_CARD" cset name='Speaker Playback Switch' "$DIREWOLF_SPEAKER_PLAYBACK_SWITCH"
amixer -c "$DIREWOLF_OUTPUT_SOUND_CARD" cset name='Speaker Playback Volume' "$DIREWOLF_SPEAKER_PLAYBACK_VOLUME"

# Log all controls for selected sound card spec
# Set Card ID for single device setup
if [ "$DIREWOLF_DUAL_SOUND_CARD" == "Yes" ] ; then
  echo -e ""
  echo -e "${LIGHT_BLUE}Actual contents set for input card $DIREWOLF_INPUT_SOUND_CARD:${NC}"
  amixer -c "$DIREWOLF_INPUT_SOUND_CARD" contents
  echo -e ""
  echo -e "${LIGHT_BLUE}Actual contents set for output card $DIREWOLF_OUTPUT_SOUND_CARD:${NC}"
  amixer -c "$DIREWOLF_OUTPUT_SOUND_CARD" contents
else
  echo -e ""
  echo -e "${LIGHT_BLUE}Actual contents set for input/output card $DIREWOLF_SOUND_CARD:${NC}"
  amixer -c "$DIREWOLF_SOUND_CARD" contents
fi
