#!/usr/bin/env python

import os
import re
import operator

from keystoneclient.v2_0 import client 
from ceilometerclient.client import get_client
from ceilometerclient.v2.options import cli_to_array
from datetime import date, timedelta

from optparse import OptionParser


def get_creds():
    return {
	'os_username': os.environ.get("OS_USERNAME"),
	'os_password': os.environ.get("OS_PASSWORD"),
	'os_tenant_name': os.environ.get("OS_TENANT_NAME"),
	'os_auth_url': os.environ.get("OS_AUTH_URL"),
    }

keystone = client.Client(username=os.environ.get('OS_USERNAME'), 
	password=os.environ.get('OS_PASSWORD'), 
	tenant_name=os.environ.get('OS_TENANT_NAME'),
        auth_url=os.environ.get('OS_AUTH_URL'))

ceilometer = get_client(2, os_username="admin", os_password="6c513ca52d694a42", os_tenant_name="admin", os_auth_url="http://192.168.20.251:5000/v2.0", region_name="RegionOne")

def matching_stats(instance_id, meters, delta):
    for meter in meters:
        for stat in ceilometer.statistics.list(meter_name=meter.get('field'),
		q=cli_to_array("resource_id={0};timestamp>{1}".format(instance_id, delta))):
	    yield getattr(operator, meter.get('op'))(meter.get('value'), stat.avg)



def parse_options():
    parser = OptionParser()
    parser.add_option("-d", "--days", dest="days", default=30,
                      help="Days delta for stats", metavar="days")

    parser.add_option("-m", "--meters", default="cpu_util<0.5",
                      dest="meters",
                      help="Meters to check, i.e: 'cpu_util<0.5'")

    parser.add_option("-e", "--exclude-tenants", default="services,admin",
                      dest="exclude_tenants")

    (options, args) = parser.parse_args()
    return options 


def main():
    options = parse_options()

    meters = cli_to_array(options.meters)
    delta = date.today() - timedelta(days=int(options.days))
    exclude_tenants = options.exclude_tenants.split(",")

    print "Looking for instances matching: {0} usage criteria on the last {1} days\n".format(options.meters, options.days)
    re_uuid = re.compile(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){4}[0-9a-f]{8}$', re.I)

    for tenant in keystone.tenants.list():
	if tenant.name in exclude_tenants:
	    continue

        for resource in ceilometer.resources.list(q=cli_to_array('project=%s' % tenant.id)):
	    if re_uuid.match(resource.resource_id):
                if all(f for f in matching_stats(resource.resource_id, meters, delta.isoformat())):
		    print "{0}, {1}".format(tenant.name, resource.resource_id)		

if __name__ == "__main__":
    main()
