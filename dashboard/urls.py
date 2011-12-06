from django.conf.urls.defaults import *
# from dashboard.views import ProjectView

urlpatterns = patterns('dashboard.views',
    url(r'^project/(?P<project>[-\w]+)/$', 'get_observations', name="get-project-observations"),
    url(r'^category/(?P<category>\w+)/$', 'get_observations', name="get-category-observations"),
    url(r'^$', 'get_observations', name="get-observations"),
)
