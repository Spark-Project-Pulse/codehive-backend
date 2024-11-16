# urls/community_urls.py
from django.urls import path
from ..views import community_views

# URL routes for calls relating to communities
urlpatterns = [
    # POST Requests
    path('createRequest/', community_views.createCommunityRequest, name='createCommunityRequest'),
    path('approveCommunityRequest/', community_views.approveCommunityRequest, name='approveCommunityRequest'),
    path('rejectCommunityRequest/', community_views.rejectCommunityRequest, name='rejectCommunityRequest'),
    path('addCommunityMember/', community_views.addCommunityMember, name='addCommunityMember'),
    path('removeCommunityMember/', community_views.removeCommunityMember, name='removeCommunityMember'),
    
    # GET Requests
    path('getAll/', community_views.getAllCommunities, name='getAllCommunities'),
    path('getAllOptions/', community_views.getAllCommunityOptions, name='getAllCommunityOptions'),
    path('getAllMembers/<str:community_id>/', community_views.getAllCommunityMembers, name='getAllCommunityMembers'),
    path('getById/<str:community_id>/', community_views.getCommunityById, name='getCommunityById'),
    path('getByTitle/<str:title>/', community_views.getCommunityByTitle, name='getCommunityByTitle'),
    path('getUserCommunitiesById/<str:user_id>/', community_views.getUserCommunitiesById, name='getUserCommunitiesById'),
    path('getAllCommunityRequests/', community_views.getAllCommunityRequests, name='getAllCommunityRequests'),
    path('userIsPartOfCommunity/<str:title>/<str:user_id>/', community_views.userIsPartOfCommunity, name='userIsPartOfCommunity'),
]
