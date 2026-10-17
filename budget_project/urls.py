from django.conf import settings
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('', include('sitepages.urls')),
    path('', include('budgeting.urls')),
]

handler404 = 'budget_project.views.handler404'
handler403 = 'budget_project.views.handler403'
handler500 = 'budget_project.views.handler500'

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
