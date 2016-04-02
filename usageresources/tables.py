from django.utils.translation import ugettext_lazy as _

from horizon import tables


class MyFilterAction(tables.FilterAction):
    name = "myfilter"


class InstancesTable(tables.DataTable):

    name = tables.Column('name', verbose_name=_("Project_Name"))
    cpu_util = tables.Column('cpu_util', verbose_name=_("CPU_Util(%)"))
    cpu_flavored = tables.Column('cpu_flavored', verbose_name=_("CPU_Flavored"))
    cpu_quota = tables.Column('cpu_quota', verbose_name=_("CPU_Quota"))
    cpu_total = tables.Column('cpu_total', verbose_name=_("CPU_Total"))

    memory_util = tables.Column('memory_util', verbose_name=_("Memory_Util(Mb)"))
    memory_flavored = tables.Column('memory_flavored', verbose_name=_("Memory_Flavored(Mb)"))
    memory_quota = tables.Column('memory_quota', verbose_name=_("Memory_Quota(Mb)"))
    memory_total = tables.Column('memory_total', verbose_name=_("Memory_Total(Mb)"))

    disk_util = tables.Column('disk_util', verbose_name=_("Disk_Util(Gb)"))
    disk_flavored = tables.Column('disk_flavored', verbose_name=_("Disk_Flavored(Gb)"))
    disk_quota = tables.Column('disk_quota', verbose_name=_("Disk_Quota(Gb)"))
    disk_total = tables.Column('disk_total', verbose_name=_("Disk_Total(Gb)"))

    class Meta:
        name = "instances"
        verbose_name = _("Instances")
        table_actions = (MyFilterAction,)















