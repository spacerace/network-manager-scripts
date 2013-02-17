#!/usr/bin/env python
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Copyright (C) 2010 Red Hat, Inc.
#


# This example prints out all the AP BSSIDs that all WiFi devices on the
# machine can see.  Useful for location-based services like Skyhook that
# can geolocate you based on the APs you can see.

import dbus
import pprint


bus = dbus.SystemBus()

# Get a proxy for the base NetworkManager object
proxy = bus.get_object("org.freedesktop.NetworkManager", "/org/freedesktop/NetworkManager")
manager = dbus.Interface(proxy, "org.freedesktop.NetworkManager")

i = 0
all_aps = []
ap_details=[["", "", "", "", "", ""],]

# Get all network devices
devices = manager.GetDevices()
for d in devices:
    dev_proxy = bus.get_object("org.freedesktop.NetworkManager", d)
    prop_iface = dbus.Interface(dev_proxy, "org.freedesktop.DBus.Properties")

    # Make sure the device is enabled before we try to use it
    state = prop_iface.Get("org.freedesktop.NetworkManager.Device", "State")
    if state <= 2:
        continue
    
    # Get device's type; we only want wifi devices
    iface = prop_iface.Get("org.freedesktop.NetworkManager.Device", "Interface")
    dtype = prop_iface.Get("org.freedesktop.NetworkManager.Device", "DeviceType")
    if dtype == 2:   # WiFi
        # Get a proxy for the wifi interface
        wifi_iface = dbus.Interface(dev_proxy, "org.freedesktop.NetworkManager.Device.Wireless")
        wifi_prop_iface = dbus.Interface(dev_proxy, "org.freedesktop.DBus.Properties")

        # Get the associated AP's object path
        connected_path = wifi_prop_iface.Get("org.freedesktop.NetworkManager.Device.Wireless", "ActiveAccessPoint")

        # Get all APs the card can see
        aps = wifi_iface.GetAccessPoints()
        for path in aps:
            ap_proxy = bus.get_object("org.freedesktop.NetworkManager", path)
            ap_prop_iface = dbus.Interface(ap_proxy, "org.freedesktop.DBus.Properties")
            bssid = ap_prop_iface.Get("org.freedesktop.NetworkManager.AccessPoint", "HwAddress")
	    ssid = ap_prop_iface.Get("org.freedesktop.NetworkManager.AccessPoint", "Ssid")
	    bitrate = ap_prop_iface.Get("org.freedesktop.NetworkManager.AccessPoint", "MaxBitrate")
	    strength =ap_prop_iface.Get("org.freedesktop.NetworkManager.AccessPoint", "Strength")	
            
	    # Cache the BSSID and fill ap_details list
            if not bssid in all_aps:
                all_aps.append(bssid)
		ap_details[i][0] = (int)(i)
		ap_details[i][1] = (str)("".join(chr(b) for b in ssid))
		#ap_details[i][2] = (str)("".join(chr(b) for b in bssid))
		ap_details[i][3] = (int)(bitrate)
		ap_details[i][4] = (int)(strength)
		ap_details[i][5] = "passXXXX"
		i += 1
    		ap_details.append(["", "", "", "", "", ""],)

		
ap_details.remove(ap_details[-1])
# and print out all APs the wifi devices can see
#print"\nFound APs:"
#for bssid in all_aps:
#    print bssid
pprint.pprint(ap_details)
