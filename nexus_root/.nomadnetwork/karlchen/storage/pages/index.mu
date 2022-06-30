#!/bin/bash
#################################################
# Set end xport color env variables
#
export RED='\033[0;31m'
export LIGHT_RED='\033[1;31m'
export GREEN='\033[0;32m'
export LIGHT_GREEN='\033[1;32m'
export YELLOW='\033[0;33m'
export LIGHT_YELLOW='\033[1;33m'
export BLUE='\033[0;34m'
export LIGHT_BLUE='\033[1;34m'
export PURPLE='\033[0;35m'
export LIGHT_PURPLE='\033[1;35m'
export CYAN='\033[0;36m'
export LIGHT_CYAN='\033[1;36m'
export NC='\033[0m' # No Color

cat $NOMADNET_CONFIG/storage/pages/banner.txt

echo
echo -e "${RED}The quick brown fox jumps over the lazy dog [RED]${NC}"
echo -e "${LIGHT_RED}The quick brown fox jumps over the lazy dog [LIGHT_RED]${NC}"
echo -e "${GREEN}The quick brown fox jumps over the lazy dog [GREEN]${NC}"
echo -e "${LIGHT_GREEN}The quick brown fox jumps over the lazy dog [LIGHT_GREEN]${NC}"
echo -e "${YELLOW}The quick brown fox jumps over the lazy dog [YELLOW]${NC}"
echo -e "${LIGHT_YELLOW}The quick brown fox jumps over the lazy dog [LIGHT_YELLOW]${NC}"
echo -e "${LIGHT_BLUE}The quick brown fox jumps over the lazy dog [LIGHT_BLUE]${NC}"
echo -e "${PURPLE}The quick brown fox jumps over the lazy dog [PURPLE]${NC}"
echo -e "${LIGHT_PURPLE}The quick brown fox jumps over the lazy dog [LIGHT_PURPLE]${NC}"
echo -e "${CYAN}The quick brown fox jumps over the lazy dog [CYAN]${NC}"
echo -e "${LIGHT_CYAN}The quick brown fox jumps over the lazy dog [LIGHT_CYAN]${NC}"

