#!/bin/bash

# This is intended to be run at bootup by the script in /etc/rc.local
#
touch log.txt
sudo bash ./scripts/start.sh > ./log.txt 2>&1 &
exit 0