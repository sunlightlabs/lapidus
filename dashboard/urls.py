from django.conf.urls.defaults import *
# from dashboard.views import ProjectView

urlpatterns = patterns('dashboard.views',
    url(r'^$', 'dashboard_list'),
)
