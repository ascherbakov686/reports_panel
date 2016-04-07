import logging
import re
import time

from horizon import views
from horizon import tables

from django.utils.datastructures import SortedDict

from openstack_dashboard.api.ceilometer import ceilometerclient as cc
from openstack_dashboard import api
from openstack_dashboard.usage import quotas

from .tables import InstancesTable

LOG = logging.getLogger(__name__)

class IndexView(tables.DataTableView):
    table_class = InstancesTable
    template_name = 'reports/usageresources/index.html'
    hvs_load_avg = []

    def get_data(self):
            instances, has_more0 = api.nova.server_list(self.request,all_tenants=True)
            tenant_list, has_more1  = api.keystone.tenant_list(self.request)
            ceiloclient = cc(self.request)
            hypervisor_list = api.nova.hypervisor_list(self.request)
            flavors = api.nova.flavor_list(self.request)
            full_flavors = SortedDict([(f.id, f) for f in flavors])

            totals = { "local_gb":0, "memory_mb":0, "vcpus":0 }
            qs = { "cores":0, "ram":0, "gigabytes":0 }

            for hv in hypervisor_list:
               uptime = api.nova.hypervisor_uptime(self.request, hv)._info
               loadavg = uptime['uptime']
               (val1,val2,val3,min1,min5,min15) = loadavg.split(',')
               (val3,min1) = min1.split(':')
               self.hvs_load_avg.append([{ "timestamp": time.time(), "hv_hostname":hv.hypervisor_hostname, "1min":min1, "5min":min5, "15min":min15 }])
               for key, value in hv.to_dict().iteritems():
                   if key in ("local_gb","memory_mb","vcpus"):
                      totals[str(key)] = value

            for tenant in tenant_list:

                quota_data = quotas.get_tenant_quota_data(self.request, tenant_id=tenant.id)
                project = { "cpu_util": 0.0, "cpu_flavored": 0, "memory_util": 0, "memory_flavored": 0, "disk_util": 0, "disk_flavored": 0 }

                for field in ("cores","ram","gigabytes"):
                    qs[str(field)] = quota_data.get(field).limit

                for instance in instances:
                    if instance and instance.tenant_id == tenant.id:
                     query = [dict(field='resource_id', op='eq', value = instance.id)]
                     cpu = ceiloclient.samples.list(meter_name='cpu_util', limit=1, q=query)
                     mem = ceiloclient.samples.list(meter_name='memory.resident', limit=1, q=query)
                     disk = ceiloclient.samples.list(meter_name='disk.allocation', limit=1, q=query)
                     project['cpu_util'] += cpu[0].counter_volume*0.1
                     project['memory_util'] += mem[0].counter_volume
                     project['disk_util'] += disk[0].counter_volume*0.000000001024

                     flavor_id = instance.flavor["id"]
                     if flavor_id in full_flavors:
                        instance.full_flavor = full_flavors[flavor_id]
                     else:
                        instance.full_flavor = api.nova.flavor_get(self.request, flavor_id)

                     project['cpu_flavored'] += instance.full_flavor.vcpus
                     project['memory_flavored'] += instance.full_flavor.ram
                     project['disk_flavored'] += instance.full_flavor.disk


                tenant.cpu_util = lambda:'-'
                setattr(tenant,"cpu_util", round(project['cpu_util'],3))
                tenant.memory_util = lambda:'-'
                setattr(tenant,"memory_util", round(project['memory_util'],3))
                tenant.disk_util = lambda:'-'
                setattr(tenant,"disk_util", round(project['disk_util'],3))

                tenant.cpu_flavored = lambda:'-'
                setattr(tenant,"cpu_flavored",project['cpu_flavored'])
                tenant.memory_flavored = lambda:'-'
                setattr(tenant,"memory_flavored",project['memory_flavored'])
                tenant.disk_flavored = lambda:'-'
                setattr(tenant,"disk_flavored",project['disk_flavored'])

                tenant.cpu_quota = lambda:'-'
                setattr(tenant,"cpu_quota",qs['cores'])
                tenant.memory_quota = lambda:'-'
                setattr(tenant,"memory_quota",qs['ram'])
                tenant.disk_quota = lambda:'-'
                setattr(tenant,"disk_quota",qs['gigabytes'])

                tenant.cpu_total = lambda:'-'
                setattr(tenant,"cpu_total",totals['vcpus'])
                tenant.memory_total = lambda:'-'
                setattr(tenant,"memory_total",totals['memory_mb'])
                tenant.disk_total = lambda:'-'
                setattr(tenant,"disk_total",totals['local_gb'])

            return tenant_list

    def get_context_data(self):
            context = super(IndexView, self).get_context_data()
            ten_list = self.get_data()

            for tenant in ten_list:
                context["cpu_free"] = tenant.cpu_total
                context["memory_free"] = tenant.memory_total
                context["disk_free"] = tenant.disk_total

            context["cpu_quota_free"] = 0
            context["memory_quota_free"] = 0
            context["disk_quota_free"] = 0

            for tenant in ten_list:
                context["cpu_quota_free"] += tenant.cpu_quota
                context["memory_quota_free"] += tenant.memory_quota
                context["disk_quota_free"] += tenant.disk_quota

            for tenant in ten_list:
                context["cpu_quota_free"] -= tenant.cpu_flavored
                context["memory_quota_free"] -= tenant.memory_flavored
                context["disk_quota_free"] -= tenant.disk_flavored

            for tenant in ten_list:
                context["cpu_free"] -= tenant.cpu_flavored
                context["memory_free"] -= tenant.memory_flavored
                context["disk_free"] -= tenant.disk_flavored

            context["stats"] = ten_list
            context["hvs_load_avg"] = self.hvs_load_avg

            return context

