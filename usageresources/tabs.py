
import logging

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tabs

from keystoneclient.client import Client as kclient 

from openstack_dashboard.api.ceilometer import ceilometerclient as cc
from openstack_dashboard import api
from openstack_dashboard.dashboards.reports.usageresources import tables

LOG = logging.getLogger(__name__)

class InstanceTab(tabs.TableTab):
    name = _("Instances Tab")
    slug = "instances_tab"
    table_classes = (tables.InstancesTable,)
    template_name = ("horizon/common/_detail_table.html")
    preload = False

    def has_more_data(self, table):
        return self._has_more

    def get_instances_data(self):
        try:
            marker = self.request.GET.get(
                        tables.InstancesTable._meta.pagination_param, None)

            instances, self._has_more = api.nova.server_list(
                self.request,
                search_opts={'marker': marker, 'paginate': True})

            ceiloclient = cc(self.request)
            
            kc = kclient(self.request)

            for instance in instances:
                query = [dict(field='resource_id', op='eq', value = instance.id)]
                value_cpu = ceiloclient.samples.list(meter_name='cpu_util', limit=1, q=query)
                value_memory = ceiloclient.samples.list(meter_name='memory.resident', limit=1, q=query)
                value_disk_allocation = ceiloclient.samples.list(meter_name='disk.allocation', limit=1, q=query)
                value_disk_read_bytes_rate = ceiloclient.samples.list(meter_name='disk.read.bytes.rate', limit=1, q=query)
                value_disk_write_bytes_rate = ceiloclient.samples.list(meter_name='disk.write.bytes.rate', limit=1, q=query)

                addresses = instance.addresses
                private = addresses['private']
                instance_name = getattr(instance, 'OS-EXT-SRV-ATTR:instance_name')
                #LOG.info(addresses)
                #LOG.info(private)
                #LOG.info(instance_name)

                resource_id = "nova-instance-" + (str)(instance_name)
                network = private[0]
                mac = network['OS-EXT-IPS-MAC:mac_addr']
                mac = mac.replace(':','')
                resource_id += "-" + mac
                query = [dict(field='resource_id', op='eq', value=resource_id)]

                value_network_outgoing_bytes_rate = ceiloclient.samples.list(meter_name='network.outgoing.bytes.rate', limit=1, q=query)
                value_network_incoming_bytes_rate = ceiloclient.samples.list(meter_name='network.incoming.bytes.rate', limit=1, q=query)

                instance.cpu = lambda:'-'
                instance.memory = lambda:'-'
                instance.disk_allocation = lambda:'-'
                instance.disk_read_bytes_rate = lambda:'-'
                instance.disk_write_bytes_rate = lambda:'-'
                instance.network_outgoing_bytes_rate = lambda:'-'
                instance.network_incoming_bytes_rate = lambda:'-'

                setattr(instance, 'cpu', value_cpu[0].counter_volume)
                setattr(instance, 'memory', value_memory[0].counter_volume)
                setattr(instance, 'disk_allocation', value_disk_allocation[0].counter_volume)
                setattr(instance, 'disk_read_bytes_rate', value_disk_read_bytes_rate[0].counter_volume)
                setattr(instance, 'disk_write_bytes_rate', value_disk_write_bytes_rate[0].counter_volume)
                setattr(instance, 'network_outgoing_bytes_rate', value_network_outgoing_bytes_rate[0].counter_volume)
                setattr(instance, 'network_incoming_bytes_rate', value_network_incoming_bytes_rate[0].counter_volume)

            #LOG.info(instances)
            return instances
        except Exception:
            self._has_more = False
            error_message = _('Unable to get instances')
            exceptions.handle(self.request, error_message)

            return []

class MypanelTabs(tabs.TabGroup):
    slug = "mypanel_tabs"
    tabs = (InstanceTab,)
    sticky = True
