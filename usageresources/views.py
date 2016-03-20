from horizon import views
from horizon import tabs

from openstack_dashboard.dashboards.reports.usageresources import tabs as report_tabs

class IndexView(tabs.TabbedTableView):
    tab_group_class = report_tabs.MypanelTabs
    # A very simple class-based view...
    template_name = 'reports/usageresources/index.html'

    def get_data(self, request, context, *args, **kwargs):
        # Add data to the context here...
        return context
