from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),  
    # ✅ Accounts app handles login, register, home, dashboard
    path('', include('accounts.urls')),  # root route for accounts
    path('accounts/', include(('accounts.urls', 'accounts'), namespace='accounts')),

    # ✅ Other apps
    path('detection/', include('detection.urls')),
    path('crop_api/', include('crop_api.urls')),
    path('camera/', include('camera.urls')),
    path('chat/', include('chatbot.urls')),  # ✅ Chatbot RAG app
]

# ✅ Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
