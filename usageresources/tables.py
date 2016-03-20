from django.utils.translation import ugettext_lazy as _

from horizon import tables


class MyFilterAction(tables.FilterAction):
    name = "myfilter"


class InstancesTable(tables.DataTable):
    name = tables.Column('name', \
                         verbose_name=_("Name"))
    status = tables.Column('status', \
                           verbose_name=_("Status"))
    zone = tables.Column('availability_zone', \
                         verbose_name=_("Availability Zone"))
    image_name = tables.Column('image_name', \
                               verbose_name=_("Image Name"))

    cpu = tables.Column('cpu', \
                               verbose_name=_("Cpu"))
    memory = tables.Column('memory', \
                               verbose_name=_("Memory"))
    disk_allocation = tables.Column('disk_allocation', \
                               verbose_name=_("Disk Allocation"))
    disk_read_bytes_rate = tables.Column('disk_read_bytes_rate', \
                               verbose_name=_("Disk Read"))
    disk_write_bytes_rate = tables.Column('disk_write_bytes_rate', \
                               verbose_name=_("Disk Write"))
    network_outgoing_bytes_rate = tables.Column('network_outgoing_bytes_rate', \
                               verbose_name=_("Network Send"))
    network_incoming_bytes_rate = tables.Column('network_incoming_bytes_rate', \
                               verbose_name=_("Network Recieve"))

    class Meta:
        name = "instances"
        verbose_name = _("Instances")
        table_actions = (MyFilterAction,)















