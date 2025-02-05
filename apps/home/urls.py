# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django.urls import path, re_path
from apps.home import views
from .views import GetProductsFromBing, HyperMax, SimilarNames, Search ,Jubran, SecoundYaserMarket, CommonWebsites, YaserMarket, GetImagesFromGoogle, Test, TestInside, ImageUploadView, StopProcess, InimexShopScrapView, MainScrapView, ArabiEmartScrapView, IntegrationTest, BashitiCentralScrapView, PetsJoScrapView, GamersScrapView, NewVisionScrapView, RealCosmeticsScrapView, DelfyScrapView, UpdateStoreScrapView, DermacolScrapView, ChangeText, ScrapView, SecScrapView, VikushaScrapView, GTSScrapView, TXONScrapView, BashitiScrapView, TemuScrapView, SportEquipmentScrapView, ACIScrapView, DiamondStarScrapView, GenerateBlog, AlrefaiScrapView
urlpatterns = [

    # The home page
    path('', views.index, name='home'),

    # Matches any html file
    re_path(r'^(?!api/).*$', views.pages, name='pages'),
    path('api/scrap', ScrapView.as_view()),
    path('api/SecScrapView', SecScrapView.as_view()),
    path('api/VikushaScrapView', VikushaScrapView.as_view()),
    path('api/GTSScrapView', GTSScrapView.as_view()),
    path('api/TXONScrapView', TXONScrapView.as_view()),
    path('api/BashitiScrapView', BashitiScrapView.as_view()),
    path('api/TemuScrapView', TemuScrapView.as_view()),
    path('api/SportEquipmentScrapView', SportEquipmentScrapView.as_view()),
    path('api/ACIScrapView', ACIScrapView.as_view()),
    path('api/DiamondStarScrapView', DiamondStarScrapView.as_view()),
    path('api/GenerateBlog', GenerateBlog.as_view()),
    path('api/AlrefaiScrapView', AlrefaiScrapView.as_view()),
    path('api/DermacolScrapView', DermacolScrapView.as_view()),
    path('api/UpdateStoreScrapView', UpdateStoreScrapView.as_view()),
    path('api/DelfyScrapView', DelfyScrapView.as_view()),
    path('api/RealCosmeticsScrapView', RealCosmeticsScrapView.as_view()),
    path('api/NewVisionScrapView', NewVisionScrapView.as_view()),
    path('api/GamersScrapView', GamersScrapView.as_view()),
    path('api/PetsJoScrapView', PetsJoScrapView.as_view()),
    path('api/BashitiCentralScrapView', BashitiCentralScrapView.as_view()),
    path('api/IntegrationTest', IntegrationTest.as_view()),
    path('api/ArabiEmartScrapView', ArabiEmartScrapView.as_view()),
    path('api/MainScrapView', MainScrapView.as_view()),
    path('api/stopProcess', StopProcess.as_view()),
    path('api/InimexShopScrapView', InimexShopScrapView.as_view()),
    path('api/ChangeText', ChangeText.as_view()),
    path('api/Test', Test.as_view()),
    path('api/YaserMarket', YaserMarket.as_view()),
    path('api/Jubran', Jubran.as_view()),
    path('api/SecoundYaserMarket', SecoundYaserMarket.as_view()),
    path('api/TestInside', TestInside.as_view()),
    path('api/GetImagesFromGoogle', GetImagesFromGoogle.as_view()),
    path('api/upload_image', ImageUploadView.as_view(), name='upload_image'),
    path('api/CommonWebsites', CommonWebsites.as_view(), name='CommonWebsites'),
    path('api/Search', Search.as_view(), name='Search'),
    path('api/SimilarNames', SimilarNames.as_view(), name='SimilarNames'),
    path('api/HyperMax', HyperMax.as_view(), name='HyperMax'),
    path('api/GetProductsFromBing', GetProductsFromBing.as_view(), name='GetProductsFromBing'),
]
