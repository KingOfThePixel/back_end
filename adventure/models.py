from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
import uuid
import random


class Item(models.Model):
    name = models.CharField(max_length=50, default="Item")


class Room(models.Model):
    n_to = models.IntegerField(null=True)
    s_to = models.IntegerField(null=True)
    e_to = models.IntegerField(null=True)
    w_to = models.IntegerField(null=True)
    x = models.IntegerField(default=0)
    y = models.IntegerField(default=0)
    is_path = models.BooleanField(default=True)
    is_spawn = models.BooleanField(default=False)
    item = models.ForeignKey(Item, on_delete=models.CASCADE, default=0)

    def connect_rooms(self, destinationRoom, direction):
        destinationRoomID = destinationRoom.id
        try:
            destinationRoom = Room.objects.get(id=destinationRoomID)
        except Room.DoesNotExist:
            print("That room does not exist")
        else:
            if direction == "n":
                self.n_to = destinationRoomID
            elif direction == "s":
                self.s_to = destinationRoomID
            elif direction == "e":
                self.e_to = destinationRoomID
            elif direction == "w":
                self.w_to = destinationRoomID
            else:
                print("Invalid direction")
                return
            self.save()

    def playerNames(self, currentPlayerID):
        return [p.user.username for p in Player.objects.filter(currentRoom=self.id) if p.id != int(currentPlayerID)]

    def playerUUIDs(self, currentPlayerID):
        return [p.uuid for p in Player.objects.filter(currentRoom=self.id) if p.id != int(currentPlayerID)]


class Player(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    currentRoom = models.IntegerField(default=0)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    x = models.IntegerField(default=0)
    y = models.IntegerField(default=0)
    sprite = models.CharField(max_length=50, null=True)
    item = models.ForeignKey(Item, on_delete=models.CASCADE, default=0)

    def initialize(self):
        if self.currentRoom == 0:
            rooms = Room.objects.all()
            spawn_rooms = [room for room in rooms if room.is_spawn == 1]
            random_room = random.randint(0, len(spawn_rooms)-1)
            self.currentRoom = spawn_rooms[random_room]
            self.save()

    def room(self):
        try:
            return Room.objects.get(id=self.currentRoom)
        except Room.DoesNotExist:
            self.initialize()
            return self.room()


@receiver(post_save, sender=User)
def create_user_player(sender, instance, created, **kwargs):
    if created:
        Player.objects.create(user=instance)
        Token.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_player(sender, instance, **kwargs):
    instance.player.save()
