from django.utils.translation import ugettext_lazy as _

import horizon
from openstack_dashboard.dashboards.reports import dashboard

class Usageresources(horizon.Panel):
    name = _("Usage Resources")
    slug = "usageresources"


dashboard.Reports.register(Usageresources)
