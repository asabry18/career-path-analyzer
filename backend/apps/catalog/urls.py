from django.urls import path

from . import api_views, views

urlpatterns = [
    path("_ping/catalog/", views.placeholder, name="catalog-ping"),
    path("skills/", api_views.SkillListView.as_view(), name="catalog-skills"),
    path("jobs/", api_views.JobListView.as_view(), name="catalog-jobs"),
    path("courses/", api_views.CourseListView.as_view(), name="catalog-courses"),
]
