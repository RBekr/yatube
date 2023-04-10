from django.contrib import admin
from django.urls import include, path, re_path
from django.conf import settings
from django.views.static import serve 

urlpatterns = (
    path('admin/', admin.site.urls),
    path('auth/', include('users.urls')),
    path('about/', include('about.urls')),
    path('auth/', include('django.contrib.auth.urls')),
    path('', include('posts.urls')),
    
)

handler404 = 'core.views.page_not_found'
handler403 = 'core.views.csrf_failure'
handler500 = 'core.views.server_error'

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += (path('__debug__/', include(debug_toolbar.urls)),) 

else:
    urlpatterns += (
        re_path(r'^media/(?P<path>.*)$', serve,{'document_root': settings.MEDIA_ROOT}), 
        re_path(r'^static/(?P<path>.*)$', serve,{'document_root': settings.STATIC_ROOT}), 
    )