import dbus,sys
from uuid import uuid4

bus = dbus.SystemBus()
nm_inst="org.freedesktop.NetworkManager"

def print_con(sets):
	print "{0}) \"{1}\"".format(sets['no'],sets['id'])
	print "    UUID: {0}".format(sets['uuid'])
	print "    Autoconnect: {0}".format(sets['autoconnect'])
	print "    Number: {0}".format(sets['number'])
	print "    APN: {0}".format(sets['apn'])

def add_nm_con(nm_id,apn,autocon):
	s_serial = dbus.Dictionary({'baud': dbus.UInt32(115200L)})
	s_gsm = dbus.Dictionary({
		'number': '*99#',
		'apn': apn})
	s_con = dbus.Dictionary({
		'id': nm_id,
		'type': 'gsm',
		'uuid': str(uuid4()),
		'autoconnect': dbus.Boolean(True) if \
			(autocon == "1" or autocon == "True" or autocon == "true") \
			else dbus.Boolean(False)
		})
	s_ip4 = dbus.Dictionary({'method': 'auto'})

	con = dbus.Dictionary({
		'serial': s_serial,
		'gsm': s_gsm,
		'connection': s_con,
		'ipv4': s_ip4})

	proxy = bus.get_object(nm_inst,"/org/freedesktop/NetworkManager/Settings")
	settings = dbus.Interface(proxy, nm_inst+".Settings")
	settings.AddConnection(con)
	return get_con_settings(con['connection']['uuid'])[0]

def get_con_settings(con_uuid="0"):
	return_con=[]
	proxy = bus.get_object(nm_inst,"/org/freedesktop/NetworkManager/Settings")
	settings = dbus.Interface(proxy, nm_inst+".Settings")
	if con_uuid == "0" or len(con_uuid) != 36:
		val = settings.ListConnections()
	else: val = [settings.GetConnectionByUuid(con_uuid)]
	for num in val:
		proxy = bus.get_object(nm_inst,num)
		connection = dbus.Interface(proxy, nm_inst+".Settings.Connection")
		con_settings = connection.GetSettings()
		con_num = num.rpartition('/')[2]
		if con_settings['connection']['type'] == 'gsm':
			return_con.append(dict({ 'no': con_num,
				'id': con_settings['connection']['id'],
				'apn': con_settings['gsm']['apn'],
				'uuid': con_settings['connection']['uuid'],
				'number': con_settings['gsm']['number'],
				'autoconnect': con_settings['connection'].get('autoconnect',"not set")}))
	return return_con

def del_nm_con(nm_uuid):
	del_con = get_con_settings(nm_uuid)[0]
	proxy = bus.get_object(nm_inst,"/org/freedesktop/NetworkManager/Settings/"+del_con['no'])
	settings = dbus.Interface(proxy, nm_inst+".Settings.Connection")
	settings.Delete()
	return del_con

if __name__ == "__main__":
	my_args = sys.argv
	if len(my_args) == 1:
		print "Usage: "+my_args[0]+" (list|add|del) PARAMETERS"
		print "List all 3G Connections: "+my_args[0]+" list [[UUID]]"
		print "Add 3G Connection: "+my_args[0]+" add [NAME] [APN] [[AUTOCONNECT]]"
		print "Remove 3G Connection: "+my_args[0]+" del [UUID]"
	elif my_args[1] == "list":
		list_uuid="0"
		if len(my_args) == 3:
			if len(my_args[2]) == 36:
				list_uuid = my_args[2]
			else:
				sys.exit("That's no proper UUID!")
		for sets in get_con_settings(list_uuid): print_con(sets)
	elif my_args[1] == "add":
		if len(my_args) <= 3:
			print "Usage: "+my_args[0]+" add [NAME] [APN] [[AUTOCONNECT]]"
		else:
			print "Added successfully!"
			autoconnect = "0"
			if len(my_args) == 5: autoconnect = my_args[4]
			print_con(add_nm_con(my_args[2],my_args[3],autoconnect))
	elif my_args[1] == "del":
		if len(my_args) == 2:
			print "Usage: "+my_args[0]+" del [UUID]"
		elif len(my_args[2]) != 36:
			sys.exit("That's no proper UUID!")
		else:
			for arg in my_args[2:]:
				print "Succesfully deleted!"
				print_con(del_nm_con(arg))

