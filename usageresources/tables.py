from django.utils.translation import ugettext_lazy as _

from horizon import tables


class MyFilterAction(tables.FilterAction):
    name = "myfilter"


class InstancesTable(tables.DataTable):

    name = tables.Column('name', verbose_name=_("Project_Name"))
    cpu_allocated = tables.Column('cpu_allocated', verbose_name=_("CPU_Allocated(%)"))
    cpu_quota = tables.Column('cpu_quota', verbose_name=_("CPU_Quota"))
    cpu_total = tables.Column('cpu_total', verbose_name=_("CPU_Total"))

    memory_allocated = tables.Column('memory_allocated', verbose_name=_("Memory_Allocated(Mb)"))
    memory_quota = tables.Column('memory_quota', verbose_name=_("Memory_Quota(Mb)"))
    memory_total = tables.Column('memory_total', verbose_name=_("Memory_Total(Mb)"))

    disk_allocated = tables.Column('disk_allocated', verbose_name=_("Disk_Allocated(Gb)"))
    disk_quota = tables.Column('disk_quota', verbose_name=_("Disk_Quota(Gb)"))
    disk_total = tables.Column('disk_total', verbose_name=_("Disk_Total(Gb)"))


    class Meta:
        name = "instances"
        verbose_name = _("Instances")
        table_actions = (MyFilterAction,)















