from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('django-admin/', admin.site.urls),   # Django default admin URL moved to /django-admin/
    path('', include('main.urls')),            # Root URL mapped to your main app's URLs (no prefix)
    path('custom-admin/', include('main.urls')),  # Custom prefix for your app's admin URLs
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
