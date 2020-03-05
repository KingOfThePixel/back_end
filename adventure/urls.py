from django.conf.urls import url
from . import api

urlpatterns = [
    url('init', api.initialize),
    url('move', api.move),
    url('say', api.say),
    url('maps', api.fetch_maps),
    url('grab', api.pick_item),
    url('drop', api.drop_item),
    url('steal', api.steal_item),

]
