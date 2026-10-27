from django.urls import path

from . import views

app_name = 'sitepages'

urlpatterns = [
    path('about/', views.about, name='about'),
    path('faq/', views.faq, name='faq'),
    path('privacy/', views.privacy, name='privacy'),
    path('terms/', views.terms, name='terms'),
    path('contact/', views.contact, name='contact'),
    path('changelog/', views.changelog, name='changelog'),
]
