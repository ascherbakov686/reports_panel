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
    cpu_util_avg = []
    mem_util_avg = []
    ten_list = []

    def get_data(self):
            instances, has_more0 = api.nova.server_list(self.request,all_tenants=True)
            tenant_list, has_more1  = api.keystone.tenant_list(self.request)
            ceiloclient = cc(self.request)
            hypervisor_list = api.nova.hypervisor_list(self.request)
            flavors = api.nova.flavor_list(self.request)
            full_flavors = SortedDict([(f.id, f) for f in flavors])

            cpu_util_avg_tmp = {}
            mem_util_avg_tmp = {}
            cpu_util_avg_tmp['cpu_util'] = []
            mem_util_avg_tmp['memory_util'] = []

            totals = { "local_gb":0, "memory_mb":0, "vcpus":0, "vcpus_flavored":0, "vcpu_util":0.0, "memory_util":0.0, }
            qs = { "cores":0, "ram":0, "gigabytes":0 }

            hvs_load_avg_list = []

            for hv in hypervisor_list:
               uptime = api.nova.hypervisor_uptime(self.request, hv)._info
               m = re.match("(.+)\sup\s+(.+),\s+(.+)\susers,\s+load average:\s(.+)", uptime['uptime'])
               if m:
                  (min1,min5,min15) = m.group(4).split(',')
                  hvs_load_avg_list.append([{"hv_hostname":hv.hypervisor_hostname, "min1":min1, "min5":min5, "min15":min15 }])
               for key, value in hv.to_dict().iteritems():
                   if key in ("local_gb","memory_mb","vcpus"):
                      totals[str(key)] = value

            hvs_load_avg_tmp = {}
            hvs_load_avg_tmp['date'] = time.time()
            for item in hvs_load_avg_list:
                it = dict(item[0])
                hv_hostname = ""
                for key,value in sorted(it.iteritems()):
                    if key == 'hv_hostname':
                       hv_hostname = value
                       hvs_load_avg_tmp[hv_hostname] = 0
                    if key == 'min15':
                       hvs_load_avg_tmp[hv_hostname] = value

            self.hvs_load_avg.append([hvs_load_avg_tmp])

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

                     flavor_id = instance.flavor["id"]
                     if flavor_id in full_flavors:
                        instance.full_flavor = full_flavors[flavor_id]
                     else:
                        instance.full_flavor = api.nova.flavor_get(self.request, flavor_id)

                     try:
                        project['cpu_flavored'] += instance.full_flavor.vcpus
                        totals['vcpus_flavored'] += instance.full_flavor.vcpus
                        project['memory_flavored'] += instance.full_flavor.ram
                        project['disk_flavored'] += instance.full_flavor.disk
                     except:
                        LOG.error("Error flavor for instance: %s" % instance.id)

                     try:
                        project['cpu_util'] += cpu[0].counter_volume * instance.full_flavor.vcpus
                        totals['vcpu_util'] += project['cpu_util']
                        project['memory_util'] += mem[0].counter_volume
                        totals['memory_util'] += project['memory_util']
                        project['disk_util'] += disk[0].counter_volume*0.000000001024
                     except Exception:
                        LOG.error("Error ceilometer for instance: %s" % instance.id)


                cpu_util_avg_tmp['cpu_util'].append(project['cpu_util'])
                mem_util_avg_tmp['memory_util'].append(project['memory_util'])

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

            self.ten_list = tenant_list

            cpu_util_avg_tmp['date'] = int(time.time())
            mem_util_avg_tmp['date'] = int(time.time())
            cpu_util_avg_tmp['cpu_util_avg'] = 100 / ((totals['vcpus_flavored'] * 100) / totals['vcpu_util'])
            mem_util_avg_tmp['memory_util_avg'] = 100 / (totals['memory_mb'] / totals['memory_util'])

            LOG.info(totals)
            LOG.info(cpu_util_avg_tmp)
            LOG.info(mem_util_avg_tmp)

            self.cpu_util_avg.append([{"date":cpu_util_avg_tmp['date'],"cpu":cpu_util_avg_tmp['cpu_util_avg']}])
            self.mem_util_avg.append([{"date":mem_util_avg_tmp['date'],"memory":mem_util_avg_tmp['memory_util_avg']}])

            return tenant_list

    def get_context_data(self):
            context = super(IndexView, self).get_context_data()

            for tenant in self.ten_list:
                context["cpu_free"] = tenant.cpu_total
                context["memory_free"] = tenant.memory_total
                context["disk_free"] = tenant.disk_total

            context["cpu_quota_free"] = 0
            context["memory_quota_free"] = 0
            context["disk_quota_free"] = 0

            for tenant in self.ten_list:
                context["cpu_quota_free"] += tenant.cpu_quota
                context["memory_quota_free"] += tenant.memory_quota
                context["disk_quota_free"] += tenant.disk_quota

            for tenant in self.ten_list:
                context["cpu_quota_free"] -= tenant.cpu_flavored
                context["memory_quota_free"] -= tenant.memory_flavored
                context["disk_quota_free"] -= tenant.disk_flavored

            for tenant in self.ten_list:
                context["cpu_free"] -= tenant.cpu_flavored
                context["memory_free"] -= tenant.memory_flavored
                context["disk_free"] -= tenant.disk_flavored

            context["stats"] = self.ten_list
            context["hvs_load_avg"] = self.hvs_load_avg
            context["cpu_util_avg"] = self.cpu_util_avg
            context["mem_util_avg"] = self.mem_util_avg

            return context

    def mean(self,numbers):
        return float( sum(numbers) / len(numbers) )
