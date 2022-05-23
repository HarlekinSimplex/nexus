#!/bin/bash
#
# This file sets the audio parameters used by DIREWOLF for communicating with the external USB sound device
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

# Set direwolf default sound config
export DIREWOLF_SOUND_CARD="${DIREWOLF_SOUND_CARD:-1}"
export DIREWOLF_SPEAKER_VOLUME="${DIREWOLF_SPEAKER_VOLUME:-80%}"
export DIREWOLF_MIC_VOLUME="${DIREWOLF_MIC_VOLUME:-80%}"
export DIREWOLF_MIC_AGC="${DIREWOLF_MIC_AGC:-off}"

# Log all sound cards available
echo -e "${LIGHT_BLUE}Sound cards available:${NC}"
aplay -l

# Log all sound cards available
echo -e "${LIGHT_BLUE}Direwolf sound configuration used:${NC}"
echo -e "DIREWOLF_SOUND_CARD=$DIREWOLF_SOUND_CARD"
echo -e "DIREWOLF_SPEAKER_VOLUME=$DIREWOLF_SPEAKER_VOLUME"
echo -e "DIREWOLF_MIC_VOLUME=$DIREWOLF_MIC_VOLUME"
echo -e "DIREWOLF_MIC_AGC=$DIREWOLF_MIC_AGC"

# Log all controls for selected sound card
echo -e "${LIGHT_BLUE}Available controls for card $DIREWOLF_SOUND_CARD:${NC}"
amixer -c "$DIREWOLF_SOUND_CARD" scontrols

# Set mixer configuration as defined
amixer -c "$DIREWOLF_SOUND_CARD" sset 'Speaker',0 "$DIREWOLF_SPEAKER_VOLUME"
amixer -c "$DIREWOLF_SOUND_CARD" sset 'Mic',0 "$DIREWOLF_MIC_VOLUME"
amixer -c "$DIREWOLF_SOUND_CARD" sset 'Auto Gain Control',0 "$DIREWOLF_MIC_AGC"

# Log all controls for selected sound card
echo -e "${LIGHT_BLUE}Sound control contents set for card $DIREWOLF_SOUND_CARD:${NC}"
amixer -c "$DIREWOLF_SOUND_CARD" contents
