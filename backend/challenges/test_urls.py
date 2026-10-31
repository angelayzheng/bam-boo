"""URL configuration used to exercise media retrieval in validator tests."""

from django.conf import settings
from django.urls import re_path
from django.views.static import serve


def serve_media(request, path):
    return serve(request, path, document_root=settings.MEDIA_ROOT)


urlpatterns = [
    re_path(r"^media/(?P<path>.*)$", serve_media),
]
