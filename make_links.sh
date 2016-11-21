#!/bin/sh
RUN_LOC=/opt/IP2LocationService/
cp $RUN_LOC/ip2loc.service /etc/systemd/system/ip2loc.service
chmod 664 /etc/systemd/system/ip2loc.service
systemctl daemon-reload
systemctl enable ip2loc.service