from django.urls import path

from . import debug_views, views

urlpatterns = [
    path("_ping/analysis/", views.placeholder, name="analysis-ping"),
    path("analyze/", views.analyze, name="analyze"),
    path(
        "test/catalog-stats/",
        debug_views.test_catalog_stats,
        name="analysis-test-catalog-stats",
    ),
    path(
        "test/cosine-example/",
        debug_views.test_cosine_example,
        name="analysis-test-cosine-example",
    ),
    path(
        "test/similarity-preview/",
        debug_views.test_similarity_preview,
        name="analysis-test-similarity-preview",
    ),
    path(
        "test/pipeline-preview/",
        debug_views.test_pipeline_preview,
        name="analysis-test-pipeline-preview",
    ),
]
