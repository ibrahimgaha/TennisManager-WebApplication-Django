from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from reservations.views import nav, footer, home

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Core authentication and dashboard URLs
    path('auth/', include('core.urls')),

    # API URLs
    path('api/', include('abonnement_salle_de_sport.urls')),
    path('api/', include('abonnement_tennis.urls')),

    # Reservations app URLs (includes new API endpoints)
    path('res/', include('reservations.urls')),

    # Match URLs
    path('', include('match.urls')),

    # Template views (keeping these here for now)
    path('navbar/', nav, name='navbar'),
    path('footer/', footer, name='footer'),

    # Home page
    path('', home, name='home'),
]


# Serve media files during development
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)