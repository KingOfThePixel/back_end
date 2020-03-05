from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from pusher import Pusher
from django.http import JsonResponse
from decouple import config
from django.contrib.auth.models import User
from .models import *
from rest_framework.decorators import api_view
import json

# instantiate pusher
pusher = Pusher(app_id=config('PUSHER_APP_ID'), key=config(
    'PUSHER_KEY'), secret=config('PUSHER_SECRET'), cluster=config('PUSHER_CLUSTER'))


@csrf_exempt
@api_view(["GET"])
def initialize(request):
    user = request.user
    player = user.player
    player_id = player.id
    uuid = player.uuid
    room_id = player.room()
    room = Room.objects.get(id=room_id)
    players = room.playerNames(player_id)
    return JsonResponse({'uuid': uuid, 'name': player.user.username, 'players': players}, safe=True)


@csrf_exempt
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
        for p_uuid in currentPlayerUUIDs:
            pusher.trigger(f'p-channel-{p_uuid}', u'broadcast', {
                           'message': f'{player.user.username} has walked {dirs[direction]}.'})
        for p_uuid in nextPlayerUUIDs:
            pusher.trigger(f'p-channel-{p_uuid}', u'broadcast', {
                           'message': f'{player.user.username} has entered from the {reverse_dirs[direction]}.'})
        return JsonResponse({'name': player.user.username, 'room': nextRoomID, 'players': players, 'error_msg': ""}, safe=True)
    else:
        players = room.playerNames(player_id)
        return JsonResponse({'name': player.user.username,  'room': nextRoomID, 'players': players, 'error_msg': "You cannot move that way."}, safe=True)


@csrf_exempt
@api_view(["POST"])
def say(request):
    player = request.user.player
    message = request.data.get("message")
    player_id = player.id
    player_uuid = player.uuid
    room = player.room()
    currentPlayerUUIDs = room.playerUUIDs(player_id)
    for p_uuid in currentPlayerUUIDs:
        pusher.trigger(f'p-channel-{p_uuid}', u'broadcast', {
                       'message': f'{player.user.username} says {message}.'})
    return JsonResponse({'name': player.user.username, 'message': message, 'players': players, 'error_msg': ""}, safe=True)


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
        return JsonResponse({'error': f"player_id:{player_id}, item_id:{item_id}, room_id:{room_id} - one of these are being recieved as a null value"}, safe=True, status=400)


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
        return JsonResponse({'error': f"player_id:{player_id}, item_id:{item_id}, room_id:{room_id} - one of these are being recieved as a null value"}, safe=True, status=400)


@api_view(["POST"])
def steal_item(request):
    victim_player_id = request.data.get("victim_player_id")
    thief_player_id = request.data.get("thief_player_id")
    item_id = request.data.get("item_id")
    if victim_player_id is not None and item_id is not None and thief_player_id is not None:
        thief_player_exists = Player.objects.filter(
            uuid=thief_player_id).exists()
        item_exists = Item.objects.filter(id=item_id).exists()
        victim_player_exists = Player.objects.filter(
            uuid=victim_player_id).exists()
        if thief_player_exists is not False and victim_player_exists is not False and item_exists is not False:
            victim_player = Player.objects.get(uuid=victim_player_id)
            if victim_player.item.id == item_id:
                thief_player = Player.objects.get(uuid=thief_player_id)
                thief_player.item_id = item_id
                thief_player.save()
                victim_player.item_id = 0
                victim_player.save()
                return JsonResponse({'message': "Thief stole item from victim item"}, safe=True, status=200)
            else:
                return JsonResponse({'error': "Victim does not have this item"}, safe=True, status=400)
        else:
            return JsonResponse({'error': f"victim_player_id:{victim_player_exists}, item_id:{item_exists}, thief_player_id:{thief_player_exists} - one of the entries do no exist in the database"}, safe=True, status=400)
    else:
        return JsonResponse({'error': f"victim_player_id:{victim_player_id}, item_id:{item_id}, thief_player_id:{thief_player_id} - one of these are being recieved as a null value"}, safe=True, status=400)
