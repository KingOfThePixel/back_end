from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
# from pusher import Pusher
from django.http import JsonResponse
from decouple import config
from django.contrib.auth.models import User
from .models import *
from rest_framework.decorators import api_view
import json

# instantiate pusher
# pusher = Pusher(app_id=config('PUSHER_APP_ID'), key=config('PUSHER_KEY'), secret=config('PUSHER_SECRET'), cluster=config('PUSHER_CLUSTER'))


@csrf_exempt
@api_view(["GET"])
def initialize(request):
    user = request.user
    player = user.player
    player_id = player.id
    uuid = player.uuid
    room = player.room()
    players = room.playerNames(player_id)
    return JsonResponse({'uuid': uuid, 'name': player.user.username, 'title': room.title, 'description': room.description, 'players': players}, safe=True)


# @csrf_exempt
@api_view(["POST"])
def move(request):
    dirs = {"n": "north", "s": "south", "e": "east", "w": "west"}
    reverse_dirs = {"n": "south", "s": "north", "e": "west", "w": "east"}
    player = request.user.player
    player_id = player.id
    player_uuid = player.uuid
    data = json.loads(request.body)
    direction = data['direction']
    room = player.room()
    nextRoomID = None
    if direction == "n":
        nextRoomID = room.n_to
    elif direction == "s":
        nextRoomID = room.s_to
    elif direction == "e":
        nextRoomID = room.e_to
    elif direction == "w":
        nextRoomID = room.w_to
    if nextRoomID is not None and nextRoomID > 0:
        nextRoom = Room.objects.get(id=nextRoomID)
        player.currentRoom = nextRoomID
        player.x = nextRoom.x
        player.y = nextRoom.y
        player.save()
        players = nextRoom.playerNames(player_id)
        currentPlayerUUIDs = room.playerUUIDs(player_id)
        nextPlayerUUIDs = nextRoom.playerUUIDs(player_id)
        # for p_uuid in currentPlayerUUIDs:
        #     pusher.trigger(f'p-channel-{p_uuid}', u'broadcast', {'message':f'{player.user.username} has walked {dirs[direction]}.'})
        # for p_uuid in nextPlayerUUIDs:
        #     pusher.trigger(f'p-channel-{p_uuid}', u'broadcast', {'message':f'{player.user.username} has entered from the {reverse_dirs[direction]}.'})
        return JsonResponse({'name': player.user.username, 'title': nextRoom.title, 'description': nextRoom.description, 'players': players, 'error_msg': ""}, safe=True)
    else:
        players = room.playerNames(player_id)
        return JsonResponse({'name': player.user.username, 'title': room.title, 'description': room.description, 'players': players, 'error_msg': "You cannot move that way."}, safe=True)


@csrf_exempt
@api_view(["POST"])
def say(request):
    # IMPLEMENT
    return JsonResponse({'error': "Not yet implemented"}, safe=True, status=500)


@api_view(["GET"])
def fetch_maps(request):
    rooms = list(Room.objects.values())
    n = 25
    final = [rooms[i * n:(i + 1) * n]
             for i in range((len(rooms) + n - 1) // n)]
    return JsonResponse({"map": final}, safe=True, status=200)


@api_view(["POST"])
def pick_item(request):
    player_id = request.data.get("player_id")
    item_id = request.data.get("item_id")
    room_id = request.data.get("room_id")
    if player_id is not None and item_id is not None and room_id is not None:
        room_exists = Room.objects.filter(id=room_id).exists()
        item_exists = Item.objects.filter(id=item_id).exists()
        player_exists = Player.objects.filter(uuid=player_id).exists()
        if room_exists is not False and player_exists is not False and item_exists is not False:
            room = Room.objects.get(id=room_id)
            if room.item.id == item_id:
                room.item_id = 0
                room.save()
                player = Player.objects.get(uuid=player_id)
                player.item_id = item_id
                player.save()
                return JsonResponse({'message': "User picked up item"}, safe=True, status=200)
            else:
                return JsonResponse({'error': "Room does not have this item"}, safe=True, status=400)
        else:
            return JsonResponse({'error': f"player_id:{player_exists}, item_id:{item_exists}, room_id:{room_exists} - one of the entries do no exist in the database"}, safe=True, status=400)
    else:
        return JsonResponse({'error': f"player_id:{player_id}, item_id:{item_id}, room_id:{room_id} - one of these are being recieved as a null value, {player}"}, safe=True, status=400)


@api_view(["POST"])
def drop_item(request):
    player_id = request.data.get("player_id")
    item_id = request.data.get("item_id")
    room_id = request.data.get("room_id")
    if player_id is not None and item_id is not None and room_id is not None:
        room_exists = Room.objects.filter(id=room_id).exists()
        item_exists = Item.objects.filter(id=item_id).exists()
        player_exists = Player.objects.filter(uuid=player_id).exists()
        if room_exists is not False and player_exists is not False and item_exists is not False:
            player = Player.objects.get(uuid=player_id)
            if player.item.id == item_id:
                room = Room.objects.get(id=room_id)
                room.item_id = item_id
                room.save()
                player.item_id = 0
                player.save()
                return JsonResponse({'message': "User dropped item"}, safe=True, status=200)
            else:
                return JsonResponse({'error': "Player does not have this item"}, safe=True, status=400)
        else:
            return JsonResponse({'error': f"player_id:{player_exists}, item_id:{item_exists}, room_id:{room_exists} - one of the entries do no exist in the database"}, safe=True, status=400)
    else:
        return JsonResponse({'error': f"player_id:{player_id}, item_id:{item_id}, room_id:{room_id} - one of these are being recieved as a null value, {player}"}, safe=True, status=400)


@api_view(["POST"])
def steal_item(request):
    victim_player_id = request.data.get("victim_player_id")
    thief_player_id = request.data.get("thief_player_id")
    item_id = request.data.get("item_id")
    if victim_player_id == null or thief_player_id == null or item_id == null:
        return JsonResponse({'error': f"victim_player_id:{victim_player_id}, item_id:{item_id}, thief_player_id:{thief_player_id} - one of these are being recieved as a null value"}, safe=True, status=400)
    """
    first recieve request, take player id victim, player id, thief item id
    victim.item will switch from 0 to 1
    thief.item will switch from 1 to 0
    """
    return JsonResponse({'error': "Not yet implemented"}, safe=True, status=500)

# edge cases item doesnt exist, players doesnt exists, room doesnt exists
# room is not walkable
# to do  - still need to figure out how to check if player or room or item does not exist and properly handling that error
