from django.utils.translation import ugettext_lazy as _

import horizon


class UsageResources(horizon.PanelGroup):
    slug = "usageresources"
    name = _("Available Reports")
    panels = ('usageresources',)


class Reports(horizon.Dashboard):
    name = _("Reports")
    slug = "reports"
    panels = (UsageResources,)  # Add your panels here.
    default_panel = 'usageresources'  # Specify the slug of the dashboard's default panel.


horizon.register(Reports)
