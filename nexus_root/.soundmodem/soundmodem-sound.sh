#!/bin/bash
#
# This file sets the audio parameters used by SOUNDMODEM for communicating with the external USB sound device
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

# Set soundmodem default sound config
export SOUNDMODEM_SOUND_CARD="${SOUNDMODEM_SOUND_CARD:-1}"
export SOUNDMODEM_SPEAKER_VOLUME="${SOUNDMODEM_SPEAKER_VOLUME:-80%}"
export SOUNDMODEM_MIC_VOLUME="${SOUNDMODEM_MIC_VOLUME:-80%}"
export SOUNDMODEM_MIC_AGC="${SOUNDMODEM_MIC_AGC:-off}"

# Log all sound cards available
echo -e ""
echo -e "${LIGHT_BLUE}Sound cards available:${NC}"
aplay -l

# Log all sound cards available
echo -e ""
echo -e "${LIGHT_BLUE}ALSA Mixer settings used:${NC}"
echo -e "SOUNDMODEM_SOUND_CARD=$SOUNDMODEM_SOUND_CARD"
echo -e "SOUNDMODEM_SPEAKER_VOLUME=$SOUNDMODEM_SPEAKER_VOLUME"
echo -e "SOUNDMODEM_MIC_VOLUME=$SOUNDMODEM_MIC_VOLUME"
echo -e "SOUNDMODEM_MIC_AGC=$SOUNDMODEM_MIC_AGC"

# Log all controls for selected sound card
echo -e ""
echo -e "${LIGHT_BLUE}Available controls for card $SOUNDMODEM_SOUND_CARD:${NC}"
amixer -c "$SOUNDMODEM_SOUND_CARD" scontrols

# Set mixer configuration as defined
amixer -c "$SOUNDMODEM_SOUND_CARD" sset 'Speaker',0 "$SOUNDMODEM_SPEAKER_VOLUME"
amixer -c "$SOUNDMODEM_SOUND_CARD" sset 'Mic',0 "$SOUNDMODEM_MIC_VOLUME"
amixer -c "$SOUNDMODEM_SOUND_CARD" sset 'Auto Gain Control',0 "$SOUNDMODEM_MIC_AGC"

# Log all controls for selected sound card
echo -e ""
echo -e "${LIGHT_BLUE}Sound control contents set for card $SOUNDMODEM_SOUND_CARD:${NC}"
amixer -c "$SOUNDMODEM_SOUND_CARD" contents
