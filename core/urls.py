"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from portfolio import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.dashboard, name='dashboard'),
    path('apps/', views.app_list, name='app_list'),
    path('apps/<int:pk>/', views.app_detail, name='app_detail'),
    path('apps/<int:pk>/mermaid/', views.generate_mermaid, name='generate_mermaid'),
    path('analysis/', views.global_analysis, name='analysis'),
    path('qa/', views.qa_view, name='qa_view'),
    path('integrations/', views.integration_list, name='integration_list'),
    path('integrations/new/', views.integration_create, name='integration_create'),
    path('integrations/<int:pk>/edit/', views.integration_update, name='integration_update'),
    path('integrations/<int:pk>/delete/', views.integration_delete, name='integration_delete'),
    path('qa/clear/', views.clear_chat, name='clear_chat'),
]