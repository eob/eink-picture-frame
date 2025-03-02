#!/bin/bash

# This is intended to be run at bootup by the script in /etc/rc.local
#
sudo bash ./scripts/start.sh > /home/ted/Desktop/eink-picture-frame/piink-log.txt 2>&1 &
exit 0