from django.conf.urls.defaults import *
from dashboard.views import ProjectView

urlpatterns = patterns('',
    url(r'^$', ProjectView.as_view()),
)
