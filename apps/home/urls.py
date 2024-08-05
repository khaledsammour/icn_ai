# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django.urls import path, re_path
from apps.home import views
from .views import ScrapView, SecScrapView, GameakScrapView, PalestinianScrapView, VikushaScrapView, GTSScrapView, TXONScrapView, CityCenterScrapView, BCIScrapView

urlpatterns = [

    # The home page
    path('', views.index, name='home'),

    # Matches any html file
    re_path(r'^(?!api/).*$', views.pages, name='pages'),
    path('api/scrap', ScrapView.as_view()),
    path('api/SecScrapView', SecScrapView.as_view()),
    path('api/GameakScrapView', GameakScrapView.as_view()),
    path('api/PalestinianScrapView', PalestinianScrapView.as_view()),
    path('api/VikushaScrapView', VikushaScrapView.as_view()),
    path('api/GTSScrapView', GTSScrapView.as_view()),
    path('api/TXONScrapView', TXONScrapView.as_view()),
    path('api/CityCenterScrapView', CityCenterScrapView.as_view()),
    path('api/BCIScrapView', BCIScrapView.as_view()),
]
