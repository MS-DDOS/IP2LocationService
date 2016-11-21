#!/bin/sh
if [ -h /usr/bin/ip2loc ]
then rm /usr/bin/ip2loc
fi
if [ -e /etc/systemd/system/ip2loc.service ]
then systemctl disable ip2loc.service && rm /etc/systemd/system/ip2loc.service
fi
if [-e /tmp/IP2LOCPID.pid ]
then rm /tmp/IP2LOCPID.pid
fi
systemctl daemon-reload