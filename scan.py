#!/usr/bin/env python

# this script scans all interfaces available to network-manager and prints out every wireless network with all available information

import dbus

bus = dbus.SystemBus()
proxy = bus.get_object("org.freedesktop.NetworkManager", "/org/freedesktop/NetworkManager")
manager = dbus.Interface(proxy, "org.freedesktop.NetworkManager")

devices = manager.GetDevices()
#print "# interface_name; interface_driver; interface_mac_addr; network_ssid; network_ap_mac_addr; network_strength; network_max_datarate; network_frequency; network_mode; network_flags; network_wpa_flags"


for d in devices:
	dev_proxy       = bus.get_object("org.freedesktop.NetworkManager", d)
	prop_iface      = dbus.Interface(dev_proxy, "org.freedesktop.DBus.Properties")

	if_state = prop_iface.Get("org.freedesktop.NetworkManager.Device", "State")
	if_name  = prop_iface.Get("org.freedesktop.NetworkManager.Device", "Interface")
	if_drv   = prop_iface.Get("org.freedesktop.NetworkManager.Device", "Driver")
	if_man   = prop_iface.Get("org.freedesktop.NetworkManager.Device", "Managed")
	if_type  = prop_iface.Get("org.freedesktop.NetworkManager.Device", "DeviceType")

	if if_state <= 2:
		continue

	if not if_man == 1:
		continue

	if not if_type == 2:
		continue

	wifi_iface = dbus.Interface(dev_proxy, "org.freedesktop.NetworkManager.Device.Wireless")
	if_hwaddr = prop_iface.Get("org.freedesktop.NetworkManager.Device.Wireless", "HwAddress")

	networks = wifi_iface.GetAccessPoints()
	for n in networks:
		network_proxy 	   = bus.get_object("org.freedesktop.NetworkManager", n)
		network_prop_iface = dbus.Interface(network_proxy, "org.freedesktop.DBus.Properties")
		nw_bssid 	   = network_prop_iface.Get("org.freedesktop.NetworkManager.AccessPoint", "HwAddress")
		nw_flags 	   = network_prop_iface.Get("org.freedesktop.NetworkManager.AccessPoint", "Flags")
		nw_wpaflags 	   = network_prop_iface.Get("org.freedesktop.NetworkManager.AccessPoint", "WpaFlags")
		nw_ssid 	   = network_prop_iface.Get("org.freedesktop.NetworkManager.AccessPoint", "Ssid")
		nw_frequency 	   = network_prop_iface.Get("org.freedesktop.NetworkManager.AccessPoint", "Frequency")
		nw_mode 	   = network_prop_iface.Get("org.freedesktop.NetworkManager.AccessPoint", "Mode")
		nw_maxrate 	   = network_prop_iface.Get("org.freedesktop.NetworkManager.AccessPoint", "MaxBitrate")
		nw_strength 	   = network_prop_iface.Get("org.freedesktop.NetworkManager.AccessPoint", "Strength")
#		print "%s;%s;%s;%s;%s;%d;%u;%u;%u;%u;%u" % (if_name, if_drv, if_hwaddr, (str)("".join(chr(b) for b in nw_ssid)), nw_bssid, nw_strength, nw_maxrate, nw_frequency, nw_mode, nw_flags, nw_wpaflags)
		print "iface=%s,%s,%s  network='%s'\t\t strength='%d' frequency='%u' mode='%u' flags='%u' wpa_flags='%u'" % (if_name,if_hwaddr,if_drv,(str)("".join(chr(b) for b in nw_ssid)), nw_strength, nw_frequency, nw_mode, nw_flags, nw_wpaflags )

