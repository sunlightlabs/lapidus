from metrics.models import Project
from django.views.generic import ListView

class ProjectView(ListView):
    model=Project
    context_object_name="project_list"
    template_name="dashboard/project_list.html"
    