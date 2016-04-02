import logging

from horizon import views
from horizon import tables

from openstack_dashboard.api.ceilometer import ceilometerclient as cc
from openstack_dashboard import api
from openstack_dashboard.usage import quotas

from .tables import InstancesTable

LOG = logging.getLogger(__name__)

class IndexView(tables.DataTableView):
    table_class = InstancesTable
    template_name = 'reports/usageresources/index.html'

    def get_data(self):

            instances, has_more0 = api.nova.server_list(self.request,all_tenants=True)
            tenant_list, has_more1  = api.keystone.tenant_list(self.request)
            ceiloclient = cc(self.request)
            hypervisor_list = api.nova.hypervisor_list(self.request)

            totals = { "local_gb":0, "memory_mb":0, "vcpus":0 }
            qs = { "cores":0, "ram":0, "gigabytes":0 }

            for hv in hypervisor_list:
               for key, value in hv.to_dict().iteritems():
                   if key in ("local_gb","memory_mb","vcpus"):
                      totals[str(key)] = value

            for tenant in tenant_list:

                quota_data = quotas.get_tenant_quota_data(self.request, tenant_id=tenant.id)
                project = { "cpu_allocated": 0.0, "memory_allocated": 0, "disk_allocated": 0 }

                for field in ("cores","ram","gigabytes"):
                    qs[str(field)] = quota_data.get(field).limit

                for instance in instances:
                    if instance and instance.tenant_id == tenant.id:
                     query = [dict(field='resource_id', op='eq', value = instance.id)]
                     cpu = ceiloclient.samples.list(meter_name='cpu_util', limit=1, q=query)
                     mem = ceiloclient.samples.list(meter_name='memory.resident', limit=1, q=query)
                     disk = ceiloclient.samples.list(meter_name='disk.allocation', limit=1, q=query)
                     project['cpu_allocated'] += cpu[0].counter_volume*0.1
                     project['memory_allocated'] += mem[0].counter_volume
                     project['disk_allocated'] += disk[0].counter_volume*0.000000001024

                tenant.cpu_allocated = lambda:'-'
                setattr(tenant,"cpu_allocated",round(project['cpu_allocated'],2))
                tenant.memory_allocated = lambda:'-'
                setattr(tenant,"memory_allocated",round(project['memory_allocated'],2))
                tenant.disk_allocated = lambda:'-'
                setattr(tenant,"disk_allocated",round(project['disk_allocated'],2))

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
    """
    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context["stats"] = self.get_data(self.request)

        return context
    """
