from django.urls import path
from .views import HelpDeskLoginView, signup_view, logout_view, profile_view

app_name = 'accounts'

urlpatterns = [
    path('login/', HelpDeskLoginView.as_view(), name='login'),
    path('signup/', signup_view, name='signup'),
    path('logout/', logout_view, name='logout'),
    path('profile/', profile_view, name='profile'),
]
