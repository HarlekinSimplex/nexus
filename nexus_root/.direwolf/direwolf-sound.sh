#!/bin/bash
#
# This file sets the audio parameters used by direwolf for communicating with the external USB sound device
#
# amixer --help
# amixer scontrols
# amixer -c 1 scontrols
#
# amixer -c 1 sset 'Speaker',0 80%
# amixer -c 1 sset 'Mic',0 70%
#
# amixer -c 1 sset 'Auto Gain Control',0 off
# amixer -c 1 sset 'Auto Gain Control',0 on
#
# amixer -c 1 contents
#
#

# Check if we have a dual device configuration set up
# Default is 'No'
export DIREWOLF_DUAL_SOUND_CARD="${DIREWOLF_DUAL_SOUND_CARD:-No}"
# Set dual device config defaults
export DIREWOLF_INPUT_SOUND_CARD="${DIREWOLF_SOUND_CARD:-1}"
export DIREWOLF_OUTPUT_SOUND_CARD="${DIREWOLF_SOUND_CARD:-1}"
# Set Input defaults
export DIREWOLF_MIC_MUTE="${DIREWOLF_SPEAKER_VOLUME:-off}"
export DIREWOLF_MIC_VOLUME="${DIREWOLF_MIC_VOLUME:-0%}"
export DIREWOLF_MIC_AGC="${DIREWOLF_MIC_AGC:-off}"
export DIREWOLF_CAPTURE_VOLUME="${DIREWOLF_CAPTURE_VOLUME:-80%}"
# Set Output defaults
export DIREWOLF_SPEAKER_VOLUME="${DIREWOLF_SPEAKER_VOLUME:-80%}"
export DIREWOLF_SPEAKER_MUTE="${DIREWOLF_SPEAKER_VOLUME:-off}"

# Set Card ID for single device setup
if [ "$DIREWOLF_DUAL_SOUND_CARD" != "Yes" ] ; then
  export DIREWOLF_INPUT_SOUND_CARD=$DIREWOLF_SOUND_CARD
  export DIREWOLF_OUTPUT_SOUND_CARD=$DIREWOLF_SOUND_CARD
fi

# Log all sound cards available
echo -e ""
echo -e "${LIGHT_BLUE}Sound cards available:${NC}"
arecord -l

# Log all sound cards available
echo -e ""
echo -e "${LIGHT_BLUE}ALSA sound device selection:${NC}"
echo -e "DIREWOLF_DUAL_SOUND_CARD=$DIREWOLF_DUAL_SOUND_CARD"
echo -e "DIREWOLF_SOUND_CARD=$DIREWOLF_SOUND_CARD"
echo -e "DIREWOLF_INPUT_SOUND_CARD=$DIREWOLF_INPUT_SOUND_CARD"
echo -e "DIREWOLF_OUTPUT_SOUND_CARD=$DIREWOLF_OUTPUT_SOUND_CARD"

echo -e "${LIGHT_BLUE}Sound input channel parameters:${NC}"
echo -e "DIREWOLF_MIC_MUTE=$DIREWOLF_MIC_MUTE"
echo -e "DIREWOLF_MIC_VOLUME=$DIREWOLF_MIC_VOLUME"
echo -e "DIREWOLF_MIC_AGC=$DIREWOLF_MIC_AGC"
echo -e "DIREWOLF_CAPTURE_VOLUME=$DIREWOLF_CAPTURE_VOLUME"

echo -e "${LIGHT_BLUE}Sound input channel parameters:${NC}"
echo -e "DIREWOLF_SPEAKER_MUTE=$DIREWOLF_SPEAKER_MUTE"
echo -e "DIREWOLF_SPEAKER_VOLUME=$DIREWOLF_SPEAKER_VOLUME"

# Log all controls for selected sound card spec
# Set Card ID for single device setup
if [ "$DIREWOLF_DUAL_SOUND_CARD" != "Yes" ] ; then
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
amixer -c "$DIREWOLF_INPUT_SOUND_CARD" cset name='Mic Capture Switch' "$DIREWOLF_MIC_MUTE"
amixer -c "$DIREWOLF_INPUT_SOUND_CARD" cset name='Mic Capture Volume' "$DIREWOLF_CAPTURE_VOLUME"
amixer -c "$DIREWOLF_INPUT_SOUND_CARD" cset name='Mic Playback Volume' "$DIREWOLF_MIC_VOLUME"
amixer -c "$DIREWOLF_INPUT_SOUND_CARD" cset name='Auto Gain Control' "$DIREWOLF_MIC_AGC"

echo -e ""
echo -e "${LIGHT_BLUE}Set output parameters:${NC}"
amixer -c "$DIREWOLF_OUTPUT_SOUND_CARD" cset name='Speaker Playback Switch' "$DIREWOLF_SPEAKER_MUTE"
amixer -c "$DIREWOLF_OUTPUT_SOUND_CARD" cset name='Speaker Playback Volume' "$DIREWOLF_SPEAKER_VOLUME"

# Log all controls for selected sound card spec
# Set Card ID for single device setup
if [ "$DIREWOLF_DUAL_SOUND_CARD" != "Yes" ] ; then
  echo -e ""
  echo -e "${LIGHT_BLUE}Sound control contents set for input card $DIREWOLF_SOUND_CARD:${NC}"
  amixer -c "$DIREWOLF_INPUT_SOUND_CARD" contents
  echo -e ""
  echo -e "${LIGHT_BLUE}Sound control contents set for output card $DIREWOLF_SOUND_CARD:${NC}"
  amixer -c "$DIREWOLF_OUTPUT_SOUND_CARD" contents
else
  echo -e ""
  echo -e "${LIGHT_BLUE}Sound control contents set for input/output card $DIREWOLF_SOUND_CARD:${NC}"
  amixer -c "$DIREWOLF_SOUND_CARD" contents
fi
