from django.conf.urls.defaults import *
# from dashboard.views import ProjectView

urlpatterns = patterns('dashboard.views',
    url(r'^(?P<from_year>\d{4})-(?P<from_month>\d{1,2})-(?P<from_day>\d{1,2})/to/(?P<to_year>\d{4})-(?P<to_month>\d{1,2})-(?P<to_day>\d{1,2})/$', 'observations_for_daterange'),
    url(r'^(?P<year>\d{4})-(?P<month>\d{1,2})-(?P<day>\d{1,2})/$', 'observations_for_day'),
    url(r'^$', 'observations_for_day'),
)
