from django.urls import include, path

from .views import RegisterView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='auth-register'),
    path('', include('dj_rest_auth.urls')),
]
