#!/bin/bash
set -e


echo '  _         _         _            _         __                        '
echo ' | |       | |       | |          | |       / /                        '
echo ' | |__  ___| |__   __| | ___   ___| | __   / / __   _____  ___   _ ___ '
echo ' | '\''_ \/ __| '\''_ \ / _'\`' |/ _ \ / __| |/ /  / / '\''_ \ / _ \ \/ / | | / __|'
echo " | |_) \\__ \\ |_) | (_| | (_) | (__|   <  / /| | | |  __/>  <| |_| \\__ \\"
echo ' |_ __/|___/_ __/ \__,_|\___/ \___|_|\_\/_/ |_| |_|\___/_/\_\\__,_|___/'
echo ""
echo "-------------------------------------------------------------"
echo " Check configuration directories"
echo "-------------------------------------------------------------"
if [ ! -d "/home/bsb/.reticulum" ]
then
    echo "Create .reticulum"
    mkdir /home/bsb/.reticulum
else
    echo ".reticulum exists"
fi
chown bsb:bsb -R ~/.reticulum
chmod -R 755 ~/.reticulum

if [ ! -d "/home/bsb/.nomadnetwork" ]
then
    echo "Create .nomadnetwork"
    mkdir /home/bsb/.nomadnetwork
else
    echo ".nomadnetwork exists"
fi
chown bsb:bsb -R ~/.nomadnetwork
chmod -R 755 ~/.nomadnetwork

if [ ! -d "/home/bsb/.nexus" ]
then
    echo "Create .nexus"
    mkdir /home/bsb/.nexus
else
    echo ".nexus exists"
fi
chown bsb:bsb -R ~/.nexus
chmod -R 755 ~/.nexus

echo ""
echo "-------------------------------------------------------------"
echo " Switch from user root to user bsb"
echo "-------------------------------------------------------------"
# Change uid and gid of node user so it matches ownership of current dir
if [ "$MAP_NODE_UID" != "no" ]; then
    if [ ! -d "$MAP_NODE_UID" ]; then
        MAP_NODE_UID=$PWD
    fi

    uid=$(stat -c '%u' "$MAP_NODE_UID")
    gid=$(stat -c '%g' "$MAP_NODE_UID")

    echo "bsb ---> UID = $uid / GID = $gid"

    export USER=bsb

    usermod -u "$uid" bsb 2> /dev/null && {
      groupmod -g "$gid" bsb 2> /dev/null || usermod -a -G "$gid" bsb
    }
fi

echo ""
echo "-------------------------------------------------------------"
echo " Run given start command using GOSU with user bsb"
echo "-------------------------------------------------------------"

echo 'gosu bsb "$@"'
exec gosu bsb "$@"
