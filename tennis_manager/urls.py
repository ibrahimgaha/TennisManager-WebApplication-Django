from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('auth/', include('core.urls')),
    path('', include('match.urls')),
    path('abonnement/', include('abonnement_salle_de_sport.urls')),
    path('admin/', admin.site.urls),
    path('api/', include('abonnement_tennis.urls')),  # Inclure les URL de l'application abonnement_tennis

]

# Serve media files during development
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)