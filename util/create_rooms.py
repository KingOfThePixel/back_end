import random
from adventure.models import Item, Player, Room
Item.objects.all().delete()
Room.objects.all().delete()
item = Item(0, "None")
item.save()
goblet = Item(1, "goblet")
goblet.save()


class World:
    def __init__(self):
        self.grid = None
        self.width = 0
        self.height = 0
    def generate_rooms(self, size_x, size_y, num_rooms):
        self.grid = [None] * size_y
        self.width = size_x
        self.height = size_y
        room_count = 0
        for i in range(len(self.grid)):
            self.grid[i] = [None] * size_x
        while room_count < num_rooms:
            x = room_count % size_x
            y = room_count // size_x
            room = Room(x=x, y=y)
            self.grid[y][x] = room
            room.save()
            room_count += 1
        rooms = Room.objects.all()
        for idx, value in enumerate(rooms):
            threshold = random.randint(0, 100)
            if threshold < 25:
                value.is_path = 0
                value.save()
            if (idx + size_x) < len(rooms):
                if value.is_path:
                    rooms[idx].connect_rooms(rooms[idx+size_x], "s")
            if (idx - size_x) >= 0:
                if value.is_path:
                    rooms[idx].connect_rooms(rooms[idx-size_x], "n")
            if idx % size_x < size_x-1:
                if value.is_path:
                    rooms[idx].connect_rooms(rooms[idx+1], "e")
            if idx % size_x > 0:
                if value.is_path:
                    rooms[idx].connect_rooms(rooms[idx-1], "w")
            x = idx % size_x
            y = idx // size_x
            self.grid[y][x] = value
        random_room = random.randint(0, len(rooms)-1)
        while rooms[random_room].is_path is 0:
            random_room = random.randint(0, len(rooms)-1)
        rooms[random_room].item_id = 1
        rooms[random_room].save()
        for i in range(4):
            random_room = random.randint(0, len(rooms)-1)
            while rooms[random_room].is_path is 0:
                random_room = random.randint(0, len(rooms)-1)
            rooms[random_room].is_spawn = 1
            rooms[random_room].save()
    def print_rooms(self):
        str = "# " * ((3 + self.width * 5) // 2) + "\n"
        reverse_grid = list(self.grid)
        for row in reverse_grid:
            str += "#"
            for room in row:
                if room is not None and room.n_to is not None:
                    str += "  |  "
                else:
                    str += "     "
            str += "#\n"
            str += "#"
            for room in row:
                if room is not None and room.w_to is not None:
                    str += "-"
                else:
                    str += " "
                if room is not None:
                    str += f"{room.id}".zfill(3)
                else:
                    str += "   "
                if room is not None and room.e_to is not None:
                    str += "-"
                else:
                    str += " "
            str += "#\n"
            str += "#"
            for room in row:
                if room is not None and room.s_to is not None:
                    str += "  |  "
                else:
                    str += "     "
            str += "#\n"
        str += "# " * ((3 + self.width * 5) // 2) + "\n"
        print(str)


w = World()
num_rooms = 625
width = 25
height = 25
w.generate_rooms(width, height, num_rooms)
w.print_rooms()
