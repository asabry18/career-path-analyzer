from django.http import JsonResponse
from django.views.decorators.http import require_GET


@require_GET
def root_json(request):
    """Minimal landing for ``/`` until a real SPA or docs page is wired."""
    return JsonResponse(
        {
            "service": "Career Path Analyzer (backend)",
            "paths": {
                "admin": request.build_absolute_uri("/admin/"),
                "skills": request.build_absolute_uri("/api/skills/"),
                "jobs": request.build_absolute_uri("/api/jobs/"),
                "courses": request.build_absolute_uri("/api/courses/"),
                "catalog_ping": request.build_absolute_uri("/api/_ping/catalog/"),
                "analysis_ping": request.build_absolute_uri("/api/_ping/analysis/"),
            },
            "hint": 'API routes live under `/api/`. Debug helpers: `/api/test/catalog-stats/` etc. when DEBUG=True.',
        }
    )
