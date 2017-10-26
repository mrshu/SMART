from django.conf.urls import url, include
from rest_framework import routers
from core.views import api

api_router = routers.DefaultRouter()
api_router.register(r'users', api.ProfileViewSet)
api_router.register(r'auth_users', api.AuthUserViewSet)
api_router.register(r'auth_groups', api.AuthUserGroupViewSet)
api_router.register(r'projects', api.ProjectViewSet)
api_router.register(r'models', api.CoreModelViewSet)
api_router.register(r'labels', api.LabelViewSet)
api_router.register(r'data', api.DataViewSet)
api_router.register(r'data_labels', api.DataLabelViewSet)
api_router.register(r'data_predictions', api.DataPredictionViewSet)
api_router.register(r'queue', api.QueueViewSet)
api_router.register(r'assigned_data', api.AssignedDataViewSet)

urlpatterns = [
    url(r'^', include(api_router.urls)),
    url(r'^get_card_deck/(?P<pk>\d+)/$', api.get_card_deck),
    url(r'^annotate_data/(?P<pk>\d+)/$', api.annotate_data),
    url(r'^leave_coding_page/$', api.leave_coding_page),
    url(r'^download_data/(?P<pk>\d+)/$', api.download_data),
    url(r'^label_distribution/(?P<pk>\d+)/$', api.label_distribution),
]