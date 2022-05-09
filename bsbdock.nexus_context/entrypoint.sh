#!/bin/bash
set -e

# Change uid and gid of node user so it matches ownership of current dir
if [ "$MAP_NODE_UID" != "no" ]; then
    if [ ! -d "$MAP_NODE_UID" ]; then
        MAP_NODE_UID=$PWD
    fi

    uid=$(stat -c '%u' "$MAP_NODE_UID")
    gid=$(stat -c '%g' "$MAP_NODE_UID")

    echo "bsb ---> UID = $uid / GID = $gid"

    export USER=bsb

    usermod -u $uid bsb 2> /dev/null && {
      groupmod -g $gid bsb 2> /dev/null || usermod -a -G $gid bsb
    }
fi

echo "**** GOSU bsb $@ ..."

exec /usr/local/bin/gosu bsb "$@"
