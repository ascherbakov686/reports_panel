# -*- encoding: utf-8 -*-

from pprint import pprint as pp
import ceilometerclient.client 
from novaclient.v2 import client
from prettytable import PrettyTable 

##Create the table
x = PrettyTable(["ID","Name","CPU_UTIL"])
x.align["ID"] = "l" 
x.padding_width = 1

#Authenticate  in Nova ICOS
nt = client.Client("admin", "6c513ca52d694a42", "admin", "http://192.168.20.251:5000/v2.0", service_type="compute",region_name="RegionOne")
#Get the list of servers running
servers = nt.servers.list(detailed=True)

#Authenticate  in Ceilometer ICOS
cclient = ceilometerclient.client.get_client(2, os_username="admin", os_password="6c513ca52d694a42", os_tenant_name="admin", os_auth_url="http://192.168.20.251:5000/v2.0",region_name="RegionOne")

#Get teh values of teh metric for each server
for server in servers:
#    print server
    query = [dict(field='resource_id', op='eq', value= server.id)]
    value_cpu = cclient.samples.list(meter_name='cpu_util', limit=1, q=query)

#    print value_cpu
    x.add_row([server.id,server.name,value_cpu[0].counter_volume])

#print the table
print x
