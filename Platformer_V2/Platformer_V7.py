import csv
import os
import random
from datetime import datetime

import arcade

# Константы
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
SCREEN_TITLE = "Платформенные головоломки"
TILE_SIZE = 64
GRAVITY = 0.8
PLAYER_JUMP_SPEED = 15
PLAYER_SPEED = 5

# Имя файла для сохранения прогресса
SAVE_FILE = "game_progress.csv"

# Глобальные текстуры для оптимизации
TEXTURES = {
    'player': None,
    'box': None,
    'button': None,
    'door': None,
    'enemy': None,
    'heart_active': None,
    'heart_inactive': None,
    'platforms': {}
}


def load_all_textures():
    TEXTURES['player'] = arcade.load_texture(
        ":resources:images/animated_characters/female_adventurer/femaleAdventurer_idle.png")
    TEXTURES['box'] = arcade.load_texture(":resources:images/tiles/boxCrate.png")
    TEXTURES['button'] = arcade.load_texture(":resources:images/tiles/stone.png")
    TEXTURES['door'] = arcade.load_texture(":resources:images/tiles/stoneCenter.png")
    TEXTURES['enemy'] = arcade.load_texture(":resources:images/enemies/slimeBlock.png")
    TEXTURES['heart_active'] = arcade.load_texture(":resources:images/items/coinGold.png")
    TEXTURES['heart_inactive'] = TEXTURES['heart_active']

    # Текстуры платформ
    TEXTURES['platforms']['grass_mid'] = arcade.load_texture(":resources:images/tiles/grassMid.png")
    TEXTURES['platforms']['grass_left'] = arcade.load_texture(":resources:images/tiles/grassLeft.png")
    TEXTURES['platforms']['grass_right'] = arcade.load_texture(":resources:images/tiles/grassRight.png")
    TEXTURES['platforms']['grass_center'] = arcade.load_texture(":resources:images/tiles/grassCenter.png")
    TEXTURES['platforms']['stone_mid'] = arcade.load_texture(":resources:images/tiles/stoneMid.png")
    TEXTURES['platforms']['stone'] = arcade.load_texture(":resources:images/tiles/stone.png")
    TEXTURES['platforms']['dirt'] = arcade.load_texture(":resources:images/tiles/dirt.png")
    TEXTURES['platforms']['dirt_mid'] = arcade.load_texture(":resources:images/tiles/dirtMid.png")
    TEXTURES['platforms']['brick'] = arcade.load_texture(":resources:images/tiles/stoneCenter.png")

    # Текстуры декораций
    TEXTURES['bush'] = arcade.load_texture(":resources:images/tiles/bush.png")
    TEXTURES['rock'] = arcade.load_texture(":resources:images/tiles/rock.png")


# Загружаем текстуры при импорте
load_all_textures()


def load_game_progress():
    progress = {
        'unlocked_levels': {1: True, 2: False, 3: False, 4: False, 5: False},
        'current_level': 1,
        'total_played_time': 0,
        'last_save': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'total_deaths': 0,
        'levels_completed': 0
    }

    try:
        if os.path.exists(SAVE_FILE):
            with open(SAVE_FILE, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    unlocked_str = row.get('unlocked_levels', '1')
                    unlocked_list = [int(x.strip()) for x in unlocked_str.split(',') if x.strip().isdigit()]

                    progress['unlocked_levels'] = {
                        1: 1 in unlocked_list,
                        2: 2 in unlocked_list,
                        3: 3 in unlocked_list,
                        4: 4 in unlocked_list,
                        5: 5 in unlocked_list
                    }

                    progress['current_level'] = int(row.get('current_level', 1))
                    progress['total_played_time'] = float(row.get('total_played_time', 0))
                    progress['last_save'] = row.get('last_save', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    progress['total_deaths'] = int(row.get('total_deaths', 0))
                    progress['levels_completed'] = int(row.get('levels_completed', 0))
    except Exception as e:
        print(f"Ошибка загрузки прогресса: {e}")

    return progress


def save_game_progress(progress):
    try:
        unlocked_levels = [str(level) for level, unlocked in progress['unlocked_levels'].items() if unlocked]
        unlocked_str = ','.join(unlocked_levels)

        data = {
            'unlocked_levels': unlocked_str,
            'current_level': progress['current_level'],
            'total_played_time': progress['total_played_time'],
            'last_save': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'total_deaths': progress['total_deaths'],
            'levels_completed': progress['levels_completed']
        }

        with open(SAVE_FILE, 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=data.keys())
            writer.writeheader()
            writer.writerow(data)

    except Exception as e:
        print(f"Ошибка сохранения прогресса: {e}")


def reset_game_progress():
    progress = {
        'unlocked_levels': {1: True, 2: False, 3: False, 4: False, 5: False},
        'current_level': 1,
        'total_played_time': 0,
        'last_save': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'total_deaths': 0,
        'levels_completed': 0
    }
    save_game_progress(progress)
    return progress


game_progress = load_game_progress()


class Player(arcade.Sprite):
    def __init__(self):
        super().__init__()
        self.texture = TEXTURES['player']
        self.width = 40
        self.height = 50
        self.center_x = 100
        self.center_y = 200
        self.speed = PLAYER_SPEED
        self.jump_speed = PLAYER_JUMP_SPEED
        self.velocity_y = 0
        self.change_x = 0
        self.on_ground = False
        self.on_wall = False
        self.health = 3
        self.max_health = 3
        self.invincible_timer = 0
        self.carrying_box = None
        self.carrying_offset_y = 40
        self.color = (255, 255, 255)

    def update(self):
        self.velocity_y -= GRAVITY
        if self.velocity_y < -20:
            self.velocity_y = -20
        self.center_y += self.velocity_y
        self.center_x += self.change_x

        self.scale = 1.0

        if self.invincible_timer <= 0:
            self.color = (255, 255, 255)
        else:
            self.invincible_timer -= 1
            self.color = (255, 0, 0) if self.invincible_timer % 10 < 5 else (255, 255, 255)

    def jump(self):
        if self.on_ground:
            self.velocity_y = self.jump_speed
            self.on_ground = False
            return True
        return False

    def wall_jump(self, direction):
        if self.on_wall:
            self.velocity_y = self.jump_speed * 0.9
            self.change_x = direction * self.speed * 1.5
            return True
        return False

    def take_damage(self):
        if self.invincible_timer <= 0:
            self.health -= 1
            self.invincible_timer = 60
            return True
        return False


class Box(arcade.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.texture = TEXTURES['box']
        self.width = 50
        self.height = 50
        self.center_x = x
        self.center_y = y
        self.can_be_pushed = True
        self.velocity_y = 0


class Button(arcade.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.texture = TEXTURES['button']
        self.width = 60
        self.height = 20
        self.center_x = x
        self.center_y = y + 40
        self.pressed = False
        self.linked_door = None
        self.color = (255, 0, 0)  # Красный

    def set_pressed(self, pressed):
        if pressed != self.pressed:
            self.pressed = pressed
            self.color = (0, 255, 0) if pressed else (255, 0, 0)  # Зеленый/Красный


class Door(arcade.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.texture = TEXTURES['door']
        self.width = 60
        self.height = 100
        self.center_x = x
        self.center_y = y + 50
        self.opened = False
        self.color = (139, 69, 19)  # Коричневый

    def set_opened(self, opened):
        if opened != self.opened:
            self.opened = opened
            self.color = (210, 180, 140) if opened else (139, 69, 19)  # Светло-коричневый/Коричневый


class Enemy(arcade.Sprite):
    def __init__(self, x, y, patrol_range=150):
        super().__init__()
        self.texture = TEXTURES['enemy']
        self.width = 40
        self.height = 40
        self.center_x = x
        self.center_y = y + 20
        self.speed = 1.5
        self.direction = 1
        self.start_x = x
        self.patrol_range = patrol_range
        self.animation_timer = 0

    def update(self):
        self.center_x += self.speed * self.direction
        self.animation_timer += 1
        if self.animation_timer >= 30:
            self.animation_timer = 0
            self.alpha = 150 if self.alpha == 255 else 255
        if abs(self.center_x - self.start_x) > self.patrol_range:
            self.direction *= -1



class Platform(arcade.Sprite):
    def __init__(self, x, y, platform_type='grass_mid'):
        super().__init__()
        self.texture = TEXTURES['platforms'].get(platform_type, TEXTURES['platforms']['grass_mid'])
        self.width = TILE_SIZE
        self.height = TILE_SIZE
        self.center_x = x + TILE_SIZE / 2
        self.center_y = y + TILE_SIZE / 2


class Decoration(arcade.Sprite):
    def __init__(self, x, y, decoration_type='bush'):
        super().__init__()

        # Определяем текстуру и размеры
        if decoration_type == 'tree':
            self.texture = TEXTURES['bush']
            self.width = 50
            self.height = 80
            self.color = (34, 139, 34)
        elif decoration_type == 'cloud':
            self.texture = TEXTURES['button']  # Используем текстуру камня
            self.width = 80
            self.height = 40
            self.color = (255, 255, 255)  # Белый
        elif decoration_type == 'rock':
            self.texture = TEXTURES['rock']
            self.width = 30
            self.height = 30
            self.color = (128, 128, 128)  # Серый
        elif decoration_type == 'lava':
            self.texture = TEXTURES['button']  # Используем текстуру камня
            self.width = 60
            self.height = 30
            self.color = (255, 69, 0)  # Красно-оранжевый
        else:  # bush
            self.texture = TEXTURES['bush']
            self.width = 40
            self.height = 25
            self.color = (0, 128, 0)  # Темно-зеленый

        self.center_x = x + self.width / 2
        self.center_y = y + self.height / 2
        self.decoration_type = decoration_type


class Heart(arcade.Sprite):
    def __init__(self, x, y, active=True):
        super().__init__()
        self.texture = TEXTURES['heart_active']
        self.width = 30
        self.height = 30
        self.center_x = x
        self.center_y = y
        self.color = (255, 0, 0) if active else (100, 100, 100)


class GameView(arcade.View):
    def __init__(self, level=1):
        super().__init__()
        self.level = level
        self.start_time = datetime.now()
        self.game_time = 0
        self.player_list = arcade.SpriteList()
        self.platform_list = arcade.SpriteList()
        self.box_list = arcade.SpriteList()
        self.button_list = arcade.SpriteList()
        self.door_list = arcade.SpriteList()
        self.enemy_list = arcade.SpriteList()
        self.heart_list = arcade.SpriteList()
        self.decoration_list = arcade.SpriteList()
        self.player = None
        self.left_pressed = self.right_pressed = self.up_pressed = False
        self.camera = arcade.camera.Camera2D()
        self.gui_camera = arcade.camera.Camera2D()
        self.game_over = False
        self.level_complete = False
        self.game_completed = False
        self.door_opened_message_timer = 0
        self.game_over_sound_played = False
        self.level_complete_sound_played = False
        self.door_sound_played = False
        self.load_sounds()
        self.setup()

    def load_sounds(self):
        try:
            self.game_over_sound = arcade.Sound(":resources:sounds/hit5.wav")
            self.level_complete_sound = arcade.Sound(":resources:sounds/coin5.wav")
            self.damage_sound = arcade.Sound(":resources:sounds/hurt5.wav")
            self.jump_sound = arcade.Sound(":resources:sounds/jump3.wav")
            self.box_sound = arcade.Sound(":resources:sounds/rockHit2.wav")
            self.button_sound = arcade.Sound(":resources:sounds/upgrade4.wav")
            self.door_sound = arcade.Sound(":resources:sounds/secret4.wav")
        except:
            self.game_over_sound = None
            self.level_complete_sound = None
            self.damage_sound = None
            self.jump_sound = None
            self.box_sound = None
            self.button_sound = None
            self.door_sound = None

    def setup(self):
        # Инициализируем списки спрайтов
        self.player_list = arcade.SpriteList()
        self.platform_list = arcade.SpriteList()
        self.box_list = arcade.SpriteList()
        self.button_list = arcade.SpriteList()
        self.door_list = arcade.SpriteList()
        self.enemy_list = arcade.SpriteList()
        self.heart_list = arcade.SpriteList()
        self.decoration_list = arcade.SpriteList()

        # Создаем игрока
        self.player = Player()
        self.player_list.append(self.player)

        # Создаем платформы
        for x in range(0, 2000, TILE_SIZE):
            platform_type = 'grass_mid'
            if x == 0:
                platform_type = 'grass_left'
            elif x >= 1900:
                platform_type = 'grass_right'
            elif x > 0 and x < 1900:
                platform_type = 'grass_center' if random.random() > 0.5 else 'grass_mid'

            platform = Platform(x, 0, platform_type)
            self.platform_list.append(platform)

            # Добавляем кусты случайным образом
            if random.random() > 0.7 and x > 100:
                bush = Decoration(x + 20, 40, 'bush')
                self.decoration_list.append(bush)

        # УРОВЕНЬ 1: Нужно скинуть коробку с высоты на кнопку
        if self.level == 1:
            self.player.center_x, self.player.center_y = 100, 150

            # Высокая платформа с коробкой
            for x in range(400, 550, TILE_SIZE):
                platform = Platform(x, 200, 'brick')
                self.platform_list.append(platform)

            # Коробка на высокой платформе
            box = Box(470, 264)
            self.box_list.append(box)

            # Лестница к высокой платформе
            for i in range(3):
                platform = Platform(200 + i * 64, 64 + i * 64, 'stone')
                self.platform_list.append(platform)

            # Кнопка
            button = Button(800, 70)
            self.button_list.append(button)

            # Дверь
            door = Door(1500, 100)
            self.door_list.append(door)
            button.linked_door = door

            # Несколько врагов на пути
            enemy1 = Enemy(600, 100, 80)
            enemy2 = Enemy(1000, 100, 80)
            self.enemy_list.append(enemy1)
            self.enemy_list.append(enemy2)

            # Лава
            lava = Decoration(1400, 50, 'lava')
            self.decoration_list.append(lava)

            # Добавляем деревья для декора
            for x in [300, 700, 1100]:
                tree = Decoration(x, 64, 'tree')
                self.decoration_list.append(tree)

        # УРОВЕНЬ 2: Лабиринт с движущимися врагами
        elif self.level == 2:
            self.player.center_x, self.player.center_y = 100, 150

            # Создаем стены-лабиринт
            for y in range(64, 400, 64):
                platform = Platform(0, y, 'stone')
                self.platform_list.append(platform)

            for y in range(64, 400, 64):
                platform = Platform(1800, y, 'stone')
                self.platform_list.append(platform)

            maze_platforms = [
                (300, 150), (500, 150), (700, 150),
                (400, 250), (600, 250),
                (300, 350), (500, 350), (700, 350),
                (900, 200), (1100, 200),
                (1000, 300),
            ]

            for i, pos in enumerate(maze_platforms):
                platform_type = 'stone' if i % 2 == 0 else 'brick'
                platform = Platform(pos[0], pos[1], platform_type)
                self.platform_list.append(platform)

            # Закрываем низ
            for x in range(0, 1700, TILE_SIZE):
                for y in range(0, 128, 64):
                    platform = Platform(x, y, 'stone')
                    self.platform_list.append(platform)

            # Коробка в начале лабиринта
            box = Box(200, 214)
            self.box_list.append(box)

            # Кнопка
            button = Button(932, 232)
            self.button_list.append(button)

            # Дверь
            door = Door(1800, 214)
            self.door_list.append(door)
            button.linked_door = door

            # Несколько врагов
            enemy_positions = [(450, 214), (650, 314), (550, 414)]

            for pos in enemy_positions:
                enemy = Enemy(pos[0], pos[1], 100)
                self.enemy_list.append(enemy)

            # Лава
            lava_positions = [(1150, 100), (1250, 100), (1350, 100)]
            for pos in lava_positions:
                lava = Decoration(pos[0], pos[1], 'lava')
                self.decoration_list.append(lava)

            # Добавляем блоки чтобы нельзя было пройти сквозь стены
            block_positions = [
                (250, 150), (550, 150), (750, 150),
                (450, 250), (650, 250),
                (350, 350), (550, 350), (750, 350),
            ]

            for pos in block_positions:
                platform = Platform(pos[0], pos[1], 'brick')
                self.platform_list.append(platform)

            # Два блока для прохода через лаву
            lava_pass_platforms = [
                (1200, 200),
                (1300, 200),
            ]

            for pos in lava_pass_platforms:
                platform = Platform(pos[0], pos[1], 'grass_center')
                self.platform_list.append(platform)

        # УРОВЕНЬ 3: Паркур с прыжками по платформам
        elif self.level == 3:
            self.player.center_x, self.player.center_y = 100, 150

            # Платформы для паркура
            parkour_platforms = [
                (200, 150, 'stone'), (400, 200, 'stone'), (600, 250, 'stone'),
                (800, 300, 'stone'), (1000, 350, 'stone'), (1200, 300, 'stone'),
                (1400, 250, 'stone'), (1600, 200, 'stone'), (1800, 150, 'stone'),
            ]

            for x, y, ptype in parkour_platforms:
                platform = Platform(x, y, ptype)
                self.platform_list.append(platform)

            # Добавляем лаву на земле
            lava_positions = [
                (300, 50), (500, 50), (900, 50),
                (1100, 50), (1500, 50), (1700, 50),
            ]

            for pos in lava_positions:
                lava = Decoration(pos[0], pos[1], 'lava')
                lava.width = 80
                self.decoration_list.append(lava)

            # Коробка
            box = Box(250, 214)
            self.box_list.append(box)

            # Кнопка
            button = Button(1632, 232)
            self.button_list.append(button)

            # Дверь
            door = Door(1900, 214)
            self.door_list.append(door)
            button.linked_door = door

            # Враги
            for i in range(3):
                x = 500 + i * 250
                enemy = Enemy(x, 264 if i % 2 == 0 else 164, 100)
                enemy.speed = 2.0
                self.enemy_list.append(enemy)

        # УРОВЕНЬ 4: Вертикальный уровень
        elif self.level == 4:
            self.player.center_x, self.player.center_y = 100, 150

            # Высокие колонны
            for x in [200, 600, 1000, 1400, 1800]:
                for y in range(0, 400, 64):
                    platform = Platform(x, y, 'stone' if x < 1000 else 'brick')
                    self.platform_list.append(platform)

            # Горизонтальные перемычки
            bridge_positions = [
                (200, 200), (600, 200), (1000, 200), (1400, 200),
                (200, 350), (600, 350), (1000, 350), (1400, 350),
            ]

            for x, y in bridge_positions:
                for dx in range(0, 350, 64):
                    platform = Platform(x + dx, y, 'grass_center')
                    self.platform_list.append(platform)

            # Коробка
            box = Box(300, 414)
            self.box_list.append(box)

            # Кнопка
            button = Button(1200, 390)
            self.button_list.append(button)

            # Дверь
            door = Door(1900, 414)
            self.door_list.append(door)
            button.linked_door = door

        # УРОВЕНЬ 5: Центральный уровень с паркуром в обе стороны
        elif self.level == 5:
            # Появляемся по центру карты
            center_x = 1000
            self.player.center_x, self.player.center_y = center_x, 150

            # Создаем пол по всей ширине карты в центре
            for x in range(0, 2000, TILE_SIZE):
                platform_type = 'grass_mid'
                if x == 0:
                    platform_type = 'grass_left'
                elif x >= 1900:
                    platform_type = 'grass_right'
                elif x > 0 and x < 1900:
                    platform_type = 'grass_center' if random.random() > 0.5 else 'grass_mid'

                platform = Platform(x, 0, platform_type)
                self.platform_list.append(platform)

            box = Box(center_x, 50)
            self.box_list.append(box)

            # ПАРКУР ВЛЕВО (2 уровня, по 4 блока каждый)
            left_parkour_level1 = [
                (center_x - 150, 150, 'stone'),
                (center_x - 300, 200, 'stone'),
                (center_x - 450, 250, 'stone'),
                (center_x - 600, 300, 'stone'),
            ]

            left_parkour_level2 = [
                (center_x - 200, 300, 'stone'),
                (center_x - 350, 350, 'stone'),
                (center_x - 500, 400, 'stone'),
                (center_x - 650, 450, 'stone'),
            ]

            # ПАРКУР ВПРАВО (2 уровня, по 4 блока каждый)
            right_parkour_level1 = [
                (center_x + 150, 150, 'stone'),
                (center_x + 300, 200, 'stone'),
                (center_x + 450, 250, 'stone'),
                (center_x + 600, 300, 'stone'),
            ]

            right_parkour_level2 = [
                (center_x + 200, 300, 'stone'),
                (center_x + 350, 350, 'stone'),
                (center_x + 500, 400, 'stone'),
                (center_x + 650, 450, 'stone'),
            ]

            # Добавляем все платформы паркура
            all_parkour = left_parkour_level1 + left_parkour_level2 + right_parkour_level1 + right_parkour_level2

            for x, y, ptype in all_parkour:
                platform = Platform(x, y, ptype)
                self.platform_list.append(platform)

            # Лава под паркуром
            for x in range(center_x - 700, center_x - 150, 80):
                lava = Decoration(x, 50, 'lava')
                lava.width = 60
                self.decoration_list.append(lava)

            for x in range(center_x + 100, center_x + 700, 80):
                lava = Decoration(x, 50, 'lava')
                lava.width = 60
                self.decoration_list.append(lava)

            # Кнопки в конце каждого паркура
            left_lower_end = center_x - 600 + 32, 300 + 32
            left_upper_end = center_x - 650 + 32, 450 + 32
            right_lower_end = center_x + 600 + 32, 300 + 32
            right_upper_end = center_x + 650 + 32, 450 + 32

            button1 = Button(left_lower_end[0], left_lower_end[1])
            button2 = Button(left_upper_end[0], left_upper_end[1])
            button3 = Button(right_lower_end[0], right_lower_end[1])
            button4 = Button(right_upper_end[0], right_upper_end[1])

            self.button_list.append(button1)
            self.button_list.append(button2)
            self.button_list.append(button3)
            self.button_list.append(button4)

            # Дверь рядом с местом появления
            door_x = center_x + 100
            door = Door(door_x, 100)
            self.door_list.append(door)

            # Связываем только правую нижнюю кнопку с дверью
            button3.linked_door = door

            # Враги на паркуре
            left_enemies = [
                (center_x - 300, 264),
                (center_x - 500, 464),
            ]

            right_enemies = [
                (center_x + 350, 414),
                (center_x + 450, 314),
            ]

            for x, y in left_enemies + right_enemies:
                enemy = Enemy(x, y, 100)
                enemy.speed = 1.5
                self.enemy_list.append(enemy)

            # Добавляем декорации
            for x in [center_x - 600, center_x + 600]:
                bush = Decoration(x, 64, 'bush')
                bush.width = 60
                bush.height = 80
                self.decoration_list.append(bush)

            for x in [center_x - 400, center_x - 200, center_x, center_x + 200, center_x + 400]:
                rock = Decoration(x, 500, 'rock')
                rock.width = 40
                rock.height = 30
                self.decoration_list.append(rock)

            for x in range(center_x - 300, center_x + 300, 80):
                if abs(x - center_x) > 50:
                    if random.random() > 0.5:
                        bush = Decoration(x, 40, 'bush')
                        self.decoration_list.append(bush)

        # Обновляем сердца
        self.update_hearts()

        # Настраиваем камеры
        self.camera.position = (self.player.center_x, self.player.center_y)
        self.gui_camera.position = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

        # Сбрасываем флаги звуков
        self.game_over_sound_played = False
        self.level_complete_sound_played = False
        self.door_sound_played = False

    def update_hearts(self):
        self.heart_list.clear()
        for i in range(self.player.max_health):
            active = i < self.player.health
            heart = Heart(40 + i * 40, SCREEN_HEIGHT - 40, active)
            self.heart_list.append(heart)

    def on_draw(self):
        self.clear()

        # Фоновый цвет для неба
        level_colors = [
            arcade.color.SKY_BLUE,
            arcade.color.LIGHT_BLUE,
            arcade.color.LAVENDER,
            arcade.color.DARK_BLUE,
            arcade.color.DARK_SLATE_GRAY
        ]
        arcade.set_background_color(level_colors[min(self.level - 1, 4)])

        if not self.game_over and not self.level_complete and not self.game_completed:
            # Активируем игровую камеру
            self.camera.use()

            # Рисуем градиентный фон
            arcade.draw_lrbt_rectangle_filled(0, 2500, 0, 600, level_colors[min(self.level - 1, 4)])

            # Рисуем солнце/луну
            sun_colors = [
                arcade.color.YELLOW,
                arcade.color.ORANGE,
                arcade.color.LIGHT_GRAY,
                arcade.color.MOONSTONE_BLUE,
                arcade.color.DARK_GRAY
            ]
            arcade.draw_circle_filled(200, 550, 50, sun_colors[min(self.level - 1, 4)])

            # Рисуем декорации
            self.decoration_list.draw()

            # Рисуем все спрайты
            self.platform_list.draw()
            self.box_list.draw()
            self.button_list.draw()
            self.door_list.draw()
            self.enemy_list.draw()
            self.player_list.draw()

            # Активируем GUI камеру
            self.gui_camera.use()
            # Рисуем UI
            self.heart_list.draw()

            arcade.draw_text(f"Уровень: {self.level}", SCREEN_WIDTH - 200, SCREEN_HEIGHT - 40,
                             arcade.color.BLACK, 18, bold=True)

            # Статистика
            arcade.draw_text(f"Смертей: {game_progress['total_deaths']}", SCREEN_WIDTH - 200, SCREEN_HEIGHT - 70,
                             arcade.color.BLACK, 14, bold=True)
            arcade.draw_text(f"Пройдено: {game_progress['levels_completed']}/5", SCREEN_WIDTH - 200,
                             SCREEN_HEIGHT - 100,
                             arcade.color.BLACK, 14, bold=True)

            # Подсказки
            if self.player.carrying_box:
                arcade.draw_text("E - бросить коробку", 50, SCREEN_HEIGHT - 100,
                                 arcade.color.BLACK, 16, bold=True)
            else:
                arcade.draw_text("E - взять коробку (когда рядом)", 50, SCREEN_HEIGHT - 100,
                                 arcade.color.BLACK, 16, bold=True)

            # Подсказка уровня
            hints = [
                "Сбросьте коробку с высоты на кнопку!",
                "Протащите коробку через лабиринт!",
                "Пронесите коробку через паркур!",
                "Поднимите коробку наверх!",
                "Нажмите кнопку коробкой!"
            ]
            hint = hints[min(self.level - 1, 4)]

            arcade.draw_text(hint, 50, SCREEN_HEIGHT - 130,
                             arcade.color.BLACK, 14, bold=True)

            # Подсказка управления
            arcade.draw_text("Управление: A/D-движение, SPACE-прыжок, E-взять/бросить",
                             50, SCREEN_HEIGHT - 160,
                             arcade.color.BLACK, 12, bold=True)

            # Проверяем, открыта ли дверь
            door_opened = False
            for door in self.door_list:
                if door.opened:
                    door_opened = True
                    break

            # Если дверь открыта, показываем сообщение
            if door_opened and self.door_opened_message_timer > 0:
                arcade.draw_text("ДВЕРЬ ОТКРЫТА", SCREEN_WIDTH // 2 - 1, SCREEN_HEIGHT - 100,
                                 arcade.color.BLACK, 24, anchor_x="center", bold=True)
                arcade.draw_text("ДВЕРЬ ОТКРЫТА", SCREEN_WIDTH // 2 + 1, SCREEN_HEIGHT - 100,
                                 arcade.color.BLACK, 24, anchor_x="center", bold=True)
                arcade.draw_text("ДВЕРЬ ОТКРЫТА", SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100 - 1,
                                 arcade.color.BLACK, 24, anchor_x="center", bold=True)
                arcade.draw_text("ДВЕРЬ ОТКРЫТА", SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100 + 1,
                                 arcade.color.BLACK, 24, anchor_x="center", bold=True)
                arcade.draw_text("ДВЕРЬ ОТКРЫТА", SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100,
                                 arcade.color.GREEN, 24, anchor_x="center", bold=True)

        elif self.game_completed:
            arcade.draw_lrbt_rectangle_filled(0, SCREEN_WIDTH, 0, SCREEN_HEIGHT, (0, 0, 0, 200))

            # Заголовок
            arcade.draw_text("ПОЗДРАВЛЯЕМ! ИГРА ПРОЙДЕНА!", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100,
                             arcade.color.GOLD, 36, anchor_x="center", bold=True)

            # Вопрос
            arcade.draw_text("Хотите сбросить прогресс и начать заново?", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30,
                             arcade.color.WHITE, 28, anchor_x="center", bold=True)

            arcade.draw_text("Y - ДА, сбросить прогресс", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30,
                             arcade.color.GREEN, 24, anchor_x="center", bold=True)
            arcade.draw_text("N - НЕТ, вернуться в меню", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 80,
                             arcade.color.RED, 24, anchor_x="center", bold=True)

            # Подсказка
            arcade.draw_text("Ваш прогресс сохранен", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 140,
                             arcade.color.LIGHT_GRAY, 20, anchor_x="center", bold=True)

        # Рисуем экран смерти
        elif self.game_over:
            arcade.draw_lrbt_rectangle_filled(0, SCREEN_WIDTH, 0, SCREEN_HEIGHT, (0, 0, 0, 200))
            arcade.draw_text("К СОЖАЛЕНИЮ, ВЫ ПОГИБЛИ", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50,
                             arcade.color.RED, 36, anchor_x="center", bold=True)
            arcade.draw_text("R - РЕСТАРТ УРОВНЯ", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
                             arcade.color.WHITE, 24, anchor_x="center", bold=True)
            arcade.draw_text("ESC - ВЫХОД В МЕНЮ", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50,
                             arcade.color.WHITE, 24, anchor_x="center", bold=True)

        # Рисуем экран завершения уровня
        elif self.level_complete and not self.game_completed:
            arcade.draw_lrbt_rectangle_filled(0, SCREEN_WIDTH, 0, SCREEN_HEIGHT, (0, 100, 0, 200))
            arcade.draw_text(f"УРОВЕНЬ {self.level} ПРОЙДЕН!", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50,
                             arcade.color.GOLD, 36, anchor_x="center", bold=True)

            # Показываем кнопку следующего уровня только если уровень разблокирован
            if self.level < 5 and game_progress['unlocked_levels'].get(self.level + 1, False):
                arcade.draw_text("SPACE - СЛЕДУЮЩИЙ УРОВЕНЬ", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
                                 arcade.color.WHITE, 24, anchor_x="center", bold=True)
            elif self.level == 5:
                arcade.draw_text("SPACE - ЗАВЕРШИТЬ ИГРУ", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
                                 arcade.color.WHITE, 24, anchor_x="center", bold=True)

            arcade.draw_text("ESC - ВЫХОД В МЕНЮ", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 80,
                             arcade.color.WHITE, 24, anchor_x="center", bold=True)

    def on_update(self, delta_time):
        # Обновляем игровое время
        self.game_time += delta_time

        if self.game_over:
            if not self.game_over_sound_played and self.game_over_sound:
                arcade.play_sound(self.game_over_sound, volume=1.0)
                self.game_over_sound_played = True
            return

        if self.level_complete or self.game_completed:
            if not self.level_complete_sound_played and self.level_complete_sound:
                arcade.play_sound(self.level_complete_sound, volume=1.0)
                self.level_complete_sound_played = True
            return

        # Обновляем таймер сообщения об открытой двери
        if self.door_opened_message_timer > 0:
            self.door_opened_message_timer -= 1

        # Движение игрока
        self.player.change_x = 0
        if self.left_pressed and not self.right_pressed:
            self.player.change_x = -self.player.speed
        elif self.right_pressed and not self.left_pressed:
            self.player.change_x = self.player.speed

        self.player.update()

        # Проверка столкновений с платформами для игрока
        self.player.on_ground = self.player.on_wall = False
        hit_list = arcade.check_for_collision_with_list(self.player, self.platform_list)
        for platform in hit_list:
            if (self.player.center_y > platform.center_y + 5 and
                    self.player.velocity_y <= 0 and
                    abs(self.player.center_x - platform.center_x) < platform.width / 2 + self.player.width / 2 - 5):

                self.player.on_ground = True
                self.player.center_y = platform.center_y + platform.height / 2 + self.player.height / 2
                self.player.velocity_y = 0
            elif abs(self.player.center_x - platform.center_x) < platform.width / 2 + self.player.width / 2 - 10:
                self.player.on_wall = True

        # Если игрок несет коробку, двигаем их
        if self.player.carrying_box:
            box = self.player.carrying_box
            box.center_x = self.player.center_x
            box.center_y = self.player.center_y + self.player.carrying_offset_y

            # Проверяем, не ударилась ли коробка о препятствие
            box_hit = arcade.check_for_collision_with_list(box, self.platform_list)
            if box_hit:
                self.player.carrying_box = None
                box.center_y -= 10

        # Физика для коробок
        for box in self.box_list:
            if self.player.carrying_box == box:
                continue

            old_y = box.center_y
            GRAVITY_BOX = GRAVITY * 5

            box.center_y -= GRAVITY_BOX

            box_hit_platforms = arcade.check_for_collision_with_list(box, self.platform_list)

            other_boxes = arcade.SpriteList()
            for other_box in self.box_list:
                if other_box != box and (not self.player.carrying_box or self.player.carrying_box != other_box):
                    other_boxes.append(other_box)

            box_hit_boxes = arcade.check_for_collision_with_list(box, other_boxes)

            if box_hit_platforms or box_hit_boxes:
                box.center_y = old_y
                box_on_ground = True

                if box_hit_platforms:
                    highest_platform = None
                    for platform in box_hit_platforms:
                        if platform.center_y < box.center_y:
                            if highest_platform is None or platform.center_y > highest_platform.center_y:
                                highest_platform = platform

                    if highest_platform:
                        box.center_y = highest_platform.center_y + highest_platform.height / 2 + box.height / 2

                if box_hit_boxes:
                    for other_box in box_hit_boxes:
                        if other_box.center_y < box.center_y:
                            box.center_y = other_box.center_y + other_box.height / 2 + box.height / 2
                            break
            else:
                box_on_ground = False

            # Движение коробок от толкания игроком
            if arcade.check_for_collision(self.player, box) and box.can_be_pushed and box_on_ground:
                dx = self.player.center_x - box.center_x

                if dx < 0:
                    if self.right_pressed:
                        old_x = box.center_x
                        box.center_x += 5

                        hit_after = arcade.check_for_collision_with_list(box, self.platform_list)

                        if not hit_after:
                            self.player.center_x = box.center_x - box.width - 5
                        else:
                            box.center_x = old_x

                else:
                    if self.left_pressed:
                        old_x = box.center_x
                        box.center_x -= 5

                        hit_after = arcade.check_for_collision_with_list(box, self.platform_list)

                        if not hit_after:
                            self.player.center_x = box.center_x + box.width + 5
                        else:
                            box.center_x = old_x

        # Кнопки
        for button in self.button_list:
            pressed = False

            for box in self.box_list:
                if arcade.check_for_collision(button, box):
                    pressed = True
                    break

            if not pressed and arcade.check_for_collision(self.player, button):
                pressed = True

            if pressed != button.pressed:
                button.set_pressed(pressed)
                if button.linked_door:
                    button.linked_door.set_opened(pressed)
                    if pressed:
                        self.door_opened_message_timer = 120
                        if self.button_sound:
                            arcade.play_sound(self.button_sound, volume=1.0)

        # Враги
        for enemy in self.enemy_list:
            enemy.update()
            if arcade.check_for_collision(self.player, enemy) and self.player.take_damage():
                self.update_hearts()
                if self.damage_sound:
                    arcade.play_sound(self.damage_sound, volume=1.0)

        # Лава
        for decoration in self.decoration_list:
            if decoration.decoration_type == 'lava':
                if arcade.check_for_collision(self.player, decoration) and self.player.take_damage():
                    self.update_hearts()
                    self.player.center_y += 20
                    self.player.velocity_y = 10
                    if self.damage_sound:
                        arcade.play_sound(self.damage_sound, volume=1.0)

        # Двери
        for door in self.door_list:
            if door.opened and arcade.check_for_collision(self.player, door):
                if not self.level_complete and not self.game_completed:
                    self.level_complete = True

                    # Обновляем прогресс
                    game_progress['current_level'] = self.level
                    game_progress['levels_completed'] += 1

                    # Разблокируем следующий уровень
                    if self.level < 5:
                        game_progress['unlocked_levels'][self.level + 1] = True
                        game_progress['current_level'] = self.level + 1
                    elif self.level == 5:
                        # Устанавливаем флаг, что все уровни пройдены
                        game_progress['levels_completed'] = 5

                    game_progress['total_played_time'] += self.game_time
                    save_game_progress(game_progress)

                    if self.door_sound and not self.door_sound_played:
                        arcade.play_sound(self.door_sound, volume=1.0)
                        self.door_sound_played = True

                    if self.level == 5:
                        self.level_complete = False
                        self.game_completed = True

        # Смерть от падения или потери здоровья
        if self.player.health <= 0 or self.player.center_y < -100:
            self.game_over = True
            game_progress['total_deaths'] += 1
            game_progress['total_played_time'] += self.game_time
            save_game_progress(game_progress)

        # Обновляем камеру
        target_x = self.player.center_x
        target_y = self.player.center_y
        current_x, current_y = self.camera.position
        new_x = current_x + (target_x - current_x) * 0.1
        new_y = current_y + (target_y - current_y) * 0.1
        new_x = max(SCREEN_WIDTH // 2, min(new_x, 2000 - SCREEN_WIDTH // 2))
        new_y = max(SCREEN_HEIGHT // 2, min(new_y, 600 - SCREEN_HEIGHT // 2))
        self.camera.position = (new_x, new_y)

    def on_key_press(self, key, modifiers):
        global game_progress
        if self.game_completed:
            if key == arcade.key.Y:
                # Сбрасываем прогресс и начинаем новую игру
                game_progress = reset_game_progress()
                self.window.show_view(GameView(1))
            elif key == arcade.key.N or key == arcade.key.ESCAPE:
                self.window.show_view(MainMenu())
            return

        if self.game_over:
            if key == arcade.key.R:
                self.setup()
                self.game_over = False
                self.game_over_sound_played = False
                self.game_time = 0
                self.start_time = datetime.now()
            elif key == arcade.key.ESCAPE:
                # Сохраняем прогресс перед выходом в меню
                game_progress['total_played_time'] += self.game_time
                save_game_progress(game_progress)
                self.window.show_view(MainMenu())
            return

        if self.level_complete:
            if key == arcade.key.SPACE and self.level < 5 and game_progress['unlocked_levels'].get(self.level + 1,
                                                                                                   False):
                # Сохраняем прогресс перед переходом на следующий уровень
                game_progress['total_played_time'] += self.game_time
                save_game_progress(game_progress)
                self.window.show_view(GameView(self.level + 1))
            elif key == arcade.key.ESCAPE:
                # Сохраняем прогресс перед выходом в меню
                game_progress['total_played_time'] += self.game_time
                save_game_progress(game_progress)
                self.window.show_view(MainMenu())
            elif self.level == 5 and key == arcade.key.SPACE:
                self.game_completed = True
            return

        if key == arcade.key.A or key == arcade.key.LEFT:
            self.left_pressed = True
        elif key == arcade.key.D or key == arcade.key.RIGHT:
            self.right_pressed = True
        elif key == arcade.key.W or key == arcade.key.UP:
            self.up_pressed = True
        elif key == arcade.key.SPACE:
            if self.player.on_wall:
                direction = -1 if self.left_pressed else 1
                self.player.wall_jump(direction)
            else:
                if self.player.jump():
                    # Проигрываем звук прыжка только при успешном прыжке
                    if self.jump_sound:
                        arcade.play_sound(self.jump_sound, volume=1.0)
        elif key == arcade.key.E:
            if self.player.carrying_box:
                self.player.carrying_box = None
                if self.box_sound:
                    arcade.play_sound(self.box_sound, volume=1.0)
            else:
                closest_box = None
                closest_distance = 50

                for box in self.box_list:
                    distance = abs(self.player.center_x - box.center_x)
                    if distance < closest_distance and abs(self.player.center_y - box.center_y) < 60:
                        closest_box = box
                        closest_distance = distance

                if closest_box:
                    self.player.carrying_box = closest_box
                    if self.box_sound:
                        arcade.play_sound(self.box_sound, volume=1.0)
        elif key == arcade.key.R:
            # Сохраняем прогресс перед рестартом
            game_progress['total_played_time'] += self.game_time
            save_game_progress(game_progress)
            self.setup()
            self.game_time = 0
            self.start_time = datetime.now()
        elif key == arcade.key.ESCAPE:
            # Сохраняем прогресс перед выходом в меню
            game_progress['total_played_time'] += self.game_time
            save_game_progress(game_progress)
            self.window.show_view(MainMenu())

    def on_key_release(self, key, modifiers):
        if key == arcade.key.A or key == arcade.key.LEFT:
            self.left_pressed = False
        elif key == arcade.key.D or key == arcade.key.RIGHT:
            self.right_pressed = False
        elif key == arcade.key.W or key == arcade.key.UP:
            self.up_pressed = False


class MainMenu(arcade.View):
    def __init__(self):
        super().__init__()
        self.selected = 0
        self.options = ["Продолжить игру", "Новая игра", "Выбор уровня", "Статистика", "Выход"]
        self.snowflakes = []
        self.snow_timer = 0

        # Загружаем звук для меню
        self.menu_select_sound = None
        self.menu_confirm_sound = None
        try:
            self.menu_select_sound = arcade.Sound(":resources:sounds/upgrade1.wav")
            self.menu_confirm_sound = arcade.Sound(":resources:sounds/upgrade4.wav")
        except:
            pass

        # Создаем снежинки
        for _ in range(100):
            self.snowflakes.append({
                'x': random.randint(0, SCREEN_WIDTH),
                'y': random.randint(0, SCREEN_HEIGHT),
                'size': random.randint(1, 3),
                'speed': random.uniform(0.2, 0.6)
            })

    def on_draw(self):
        self.clear()

        arcade.draw_lrbt_rectangle_filled(0, SCREEN_WIDTH, 0, SCREEN_HEIGHT, arcade.color.DARK_BLUE)

        for flake in self.snowflakes:
            arcade.draw_circle_filled(flake['x'], flake['y'], flake['size'], arcade.color.WHITE)

        title_text = "ПЛАТФОРМЕННЫЕ ГОЛОВОЛОМКИ"
        title_x = SCREEN_WIDTH // 2
        title_y = SCREEN_HEIGHT * 0.75

        arcade.draw_text(title_text, title_x, title_y,
                         arcade.color.GOLD, 42, anchor_x="center", anchor_y="center",
                         font_name="Arial", bold=True)

        # Показываем текущий прогресс
        current_level = game_progress['current_level']
        unlocked_count = sum(1 for level, unlocked in game_progress['unlocked_levels'].items() if unlocked)
        arcade.draw_text(f"Текущий уровень: {current_level}", title_x, title_y - 50,
                         arcade.color.LIGHT_GREEN, 20, anchor_x="center", anchor_y="center",
                         font_name="Arial", bold=True)
        arcade.draw_text(f"Прогресс: {unlocked_count}/5 уровней", title_x, title_y - 80,
                         arcade.color.LIGHT_BLUE, 18, anchor_x="center", anchor_y="center",
                         font_name="Arial", bold=True)

        menu_start_y = SCREEN_HEIGHT * 0.45

        for i, option in enumerate(self.options):
            color = arcade.color.BLACK if i == self.selected else arcade.color.WHITE

            item_x = SCREEN_WIDTH // 2
            item_y = menu_start_y - i * 60

            arcade.draw_text(option, item_x, item_y,
                             color, 30,
                             anchor_x="center", anchor_y="center",
                             font_name="Arial", bold=True)

        hint_text = "W/S-выбор, ENTER-подтвердить, ESC-выход"
        hint_x = SCREEN_WIDTH // 2
        hint_y = 60

        arcade.draw_text(hint_text, hint_x, hint_y,
                         arcade.color.LIGHT_GRAY, 18,
                         anchor_x="center", anchor_y="center",
                         font_name="Arial", bold=True)

    def on_update(self, delta_time):
        self.snow_timer += delta_time
        if self.snow_timer > 0.05:
            self.snow_timer = 0
            for flake in self.snowflakes:
                flake['y'] -= flake['speed']
                if flake['y'] < 0:
                    flake['y'] = SCREEN_HEIGHT
                    flake['x'] = random.randint(0, SCREEN_WIDTH)

    def on_key_press(self, key, modifiers):
        global game_progress

        old_selected = self.selected

        if key == arcade.key.W:
            self.selected = (self.selected - 1) % len(self.options)
            # Звук выбора пункта
            if self.selected != old_selected and self.menu_select_sound:
                arcade.play_sound(self.menu_select_sound, volume=1.0)
        elif key == arcade.key.S:
            self.selected = (self.selected + 1) % len(self.options)
            if self.selected != old_selected and self.menu_select_sound:
                arcade.play_sound(self.menu_select_sound, volume=1.0)
        elif key == arcade.key.ENTER or key == arcade.key.SPACE:
            # Звук подтверждения
            if self.menu_confirm_sound:
                arcade.play_sound(self.menu_confirm_sound, volume=1.0)

            if self.selected == 0:
                current_level = game_progress['current_level']
                self.window.show_view(GameView(current_level))
            elif self.selected == 1:
                # Сбрасываем прогресс
                game_progress = reset_game_progress()
                self.window.show_view(GameView(1))
            elif self.selected == 2:
                self.window.show_view(LevelSelectView())
            elif self.selected == 3:
                self.window.show_view(StatisticsView())
            elif self.selected == 4:
                arcade.exit()
        elif key == arcade.key.ESCAPE:
            arcade.exit()


class StatisticsView(arcade.View):
    def __init__(self):
        super().__init__()
        self.snowflakes = []

        for _ in range(50):
            self.snowflakes.append({
                'x': random.randint(0, SCREEN_WIDTH),
                'y': random.randint(0, SCREEN_HEIGHT),
                'size': random.randint(1, 3),
                'speed': random.uniform(0.2, 0.6)
            })

    def on_draw(self):
        self.clear()

        arcade.draw_lrbt_rectangle_filled(0, SCREEN_WIDTH, 0, SCREEN_HEIGHT, arcade.color.DARK_BLUE)

        for flake in self.snowflakes:
            arcade.draw_circle_filled(flake['x'], flake['y'], flake['size'], arcade.color.WHITE)

        title_x = SCREEN_WIDTH // 2
        title_y = SCREEN_HEIGHT * 0.85

        arcade.draw_text("СТАТИСТИКА ИГРЫ", title_x, title_y,
                         arcade.color.GOLD, 42, anchor_x="center", anchor_y="center",
                         font_name="Arial", bold=True)

        # Отображаем статистику
        stats_y = SCREEN_HEIGHT * 0.65
        stats = [
            ("Текущий уровень:", f"{game_progress['current_level']}/5"),
            ("Разблокировано уровней:",
             f"{sum(1 for level, unlocked in game_progress['unlocked_levels'].items() if unlocked)}/5"),
            ("Всего пройдено уровней:", f"{game_progress['levels_completed']}"),
            ("Всего смертей:", f"{game_progress['total_deaths']}"),
            ("Общее время игры:", f"{game_progress['total_played_time']:.1f} сек"),
            ("Последнее сохранение:", game_progress['last_save']),
        ]

        for i, (label, value) in enumerate(stats):
            y_pos = stats_y - i * 50
            arcade.draw_text(label, title_x - 200, y_pos,
                             arcade.color.WHITE, 22, anchor_x="right", anchor_y="center",
                             font_name="Arial", bold=True)
            arcade.draw_text(value, title_x - 180, y_pos,
                             arcade.color.LIGHT_GREEN, 22, anchor_x="left", anchor_y="center",
                             font_name="Arial", bold=True)

        # Разблокированные уровни
        unlocked_y = SCREEN_HEIGHT * 0.3
        arcade.draw_text("РАЗБЛОКИРОВАННЫЕ УРОВНИ:", title_x, unlocked_y,
                         arcade.color.WHITE, 26, anchor_x="center", anchor_y="center",
                         font_name="Arial", bold=True)

        levels_y = unlocked_y - 50
        for i in range(1, 6):
            level_x = title_x + (i - 3) * 100
            if game_progress['unlocked_levels'].get(i, False):
                color = arcade.color.GREEN
                text = f"{i}"
            else:
                color = arcade.color.RED
                text = f"{i}"

            arcade.draw_text(text, level_x, levels_y,
                             color, 40, anchor_x="center", anchor_y="center",
                             font_name="Arial", bold=True)

            # Добавляем иконку разблокировки/блокировки под цифрой
            icon_y = levels_y - 40
            if game_progress['unlocked_levels'].get(i, False):
                arcade.draw_text("✓", level_x, icon_y,
                                 arcade.color.GREEN, 30, anchor_x="center", anchor_y="center",
                                 font_name="Arial", bold=True)
            else:
                arcade.draw_text("✗", level_x, icon_y,
                                 arcade.color.RED, 30, anchor_x="center", anchor_y="center",
                                 font_name="Arial", bold=True)

        # Подсказка
        hint_y = 80
        arcade.draw_text("ESC - вернуться в меню", title_x, hint_y,
                         arcade.color.LIGHT_GRAY, 20, anchor_x="center", anchor_y="center",
                         font_name="Arial", bold=True)

    def on_update(self, delta_time):
        for flake in self.snowflakes:
            flake['y'] -= flake['speed']
            if flake['y'] < 0:
                flake['y'] = SCREEN_HEIGHT
                flake['x'] = random.randint(0, SCREEN_WIDTH)

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            self.window.show_view(MainMenu())


class LevelSelectView(arcade.View):
    def __init__(self):
        super().__init__()
        self.selected = 1
        self.snowflakes = []

        # Загружаем звук для выбора уровня
        self.level_select_sound = None
        self.level_confirm_sound = None
        try:
            self.level_select_sound = arcade.Sound(":resources:sounds/upgrade1.wav")
            self.level_confirm_sound = arcade.Sound(":resources:sounds/upgrade4.wav")
        except:
            try:
                # Создаем простые звуки вручную
                self.level_select_sound = self.create_beep_sound(600, 50)
                self.level_confirm_sound = self.create_beep_sound(800, 100)
            except:
                pass

        for _ in range(50):
            self.snowflakes.append({
                'x': random.randint(0, SCREEN_WIDTH),
                'y': random.randint(0, SCREEN_HEIGHT),
                'size': random.randint(1, 3),
                'speed': random.uniform(0.2, 0.6)
            })

    def create_beep_sound(self, frequency=440, duration_ms=100):
        try:
            import numpy as np

            sample_rate = 44100
            duration = duration_ms / 1000.0
            num_samples = int(sample_rate * duration)

            t = np.linspace(0, duration, num_samples, False)
            wave = np.sin(frequency * 2 * np.pi * t)

            envelope = np.ones_like(wave)
            attack_len = int(0.05 * sample_rate)
            release_len = int(0.1 * sample_rate)

            for i in range(attack_len):
                envelope[i] = i / attack_len

            for i in range(release_len):
                envelope[-i - 1] = i / release_len

            wave = wave * envelope
            wave = (wave * 32767).astype(np.int16).tobytes()

            sound = arcade.Sound(wave, streaming=False)
            return sound
        except:
            return None

    def on_draw(self):
        self.clear()

        arcade.draw_lrbt_rectangle_filled(0, SCREEN_WIDTH, 0, SCREEN_HEIGHT, arcade.color.DARK_BLUE)

        for flake in self.snowflakes:
            arcade.draw_circle_filled(flake['x'], flake['y'], flake['size'], arcade.color.WHITE)

        arcade.draw_text("ВЫБОР УРОВНЯ", SCREEN_WIDTH // 2,
                         SCREEN_HEIGHT * 0.85, arcade.color.GOLD, 42, anchor_x="center",
                         font_name="Arial", bold=True)

        for i in range(1, 6):
            is_unlocked = game_progress['unlocked_levels'].get(i, False)
            is_selected = i == self.selected
            is_current = i == game_progress['current_level']

            # Цвета для уровней
            if is_unlocked:
                level_colors = [
                    arcade.color.GREEN,
                    arcade.color.BLUE,
                    arcade.color.PURPLE,
                    arcade.color.ORANGE,
                    arcade.color.RED
                ]
                border_color = arcade.color.YELLOW if is_selected else arcade.color.WHITE
                text_color = arcade.color.BLACK if is_selected else arcade.color.WHITE
                level_color = level_colors[i - 1]
            else:
                # Заблокированные уровни - серые
                border_color = arcade.color.DARK_GRAY if is_selected else arcade.color.GRAY
                text_color = arcade.color.DARK_GRAY
                level_color = arcade.color.DARK_GRAY

            level_names = [
                "Сброс коробки",
                "Лабиринт",
                "Паркур",
                "Вертикаль",
                "Финальный"
            ]

            level_x = SCREEN_WIDTH // 2 + (i - 3) * 150
            level_y = SCREEN_HEIGHT // 2

            arcade.draw_lbwh_rectangle_filled(level_x - 60, level_y - 60, 120, 120, border_color)
            arcade.draw_lbwh_rectangle_filled(level_x - 60, level_y - 60, 120, 120, level_color)
            arcade.draw_text(str(i), level_x, level_y,
                             text_color, 48, anchor_x="center", anchor_y="center",
                             font_name="Arial", bold=True)

            # Текущий уровень отмечаем звездочкой
            if is_current and is_unlocked:
                arcade.draw_text("★", level_x, level_y + 30,
                                 arcade.color.YELLOW, 30, anchor_x="center", anchor_y="center",
                                 font_name="Arial", bold=True)

            # Замок для заблокированных уровней
            if not is_unlocked:
                arcade.draw_text("🔒", level_x, level_y + 20,
                                 arcade.color.WHITE, 30, anchor_x="center", anchor_y="center",
                                 font_name="Arial")

            text_bg_y = level_y - 80
            arcade.draw_text(level_names[i - 1], level_x, text_bg_y,
                             arcade.color.WHITE, 14, anchor_x="center", anchor_y="center",
                             font_name="Arial", bold=True)

            # Статус разблокировки
            if not is_unlocked:
                arcade.draw_text("Заблокирован", level_x, text_bg_y - 25,
                                 arcade.color.LIGHT_GRAY, 12, anchor_x="center", anchor_y="center",
                                 font_name="Arial")
            elif is_current:
                arcade.draw_text("Текущий", level_x, text_bg_y - 25,
                                 arcade.color.YELLOW, 12, anchor_x="center", anchor_y="center",
                                 font_name="Arial", bold=True)

        arcade.draw_text("A/D-выбор, ENTER-играть, ESC-назад", SCREEN_WIDTH // 2,
                         100, arcade.color.LIGHT_GRAY, 20, anchor_x="center", anchor_y="center",
                         font_name="Arial", bold=True)

        # Статистика прогресса
        unlocked_count = sum(1 for level, unlocked in game_progress['unlocked_levels'].items() if unlocked)
        arcade.draw_text(f"Прогресс: {unlocked_count}/5 уровней разблокировано", SCREEN_WIDTH // 2,
                         60, arcade.color.LIGHT_GREEN, 18, anchor_x="center", anchor_y="center",
                         font_name="Arial", bold=True)

    def on_update(self, delta_time):
        for flake in self.snowflakes:
            flake['y'] -= flake['speed']
            if flake['y'] < 0:
                flake['y'] = SCREEN_HEIGHT
                flake['x'] = random.randint(0, SCREEN_WIDTH)

    def on_key_press(self, key, modifiers):
        old_selected = self.selected

        if key == arcade.key.A:
            self.selected = max(1, self.selected - 1)
            # Звук выбора уровня
            if self.selected != old_selected and self.level_select_sound:
                arcade.play_sound(self.level_select_sound, volume=1.0)
        elif key == arcade.key.D:
            self.selected = min(5, self.selected + 1)
            if self.selected != old_selected and self.level_select_sound:
                arcade.play_sound(self.level_select_sound, volume=1.0)
        elif key == arcade.key.ENTER or key == arcade.key.SPACE:
            # Проверяем, разблокирован ли уровень
            if game_progress['unlocked_levels'].get(self.selected, False):
                if self.level_confirm_sound:
                    arcade.play_sound(self.level_confirm_sound, volume=1.0)
                # Обновляем текущий уровень
                game_progress['current_level'] = self.selected
                save_game_progress(game_progress)
                self.window.show_view(GameView(self.selected))
            else:
                # Звук ошибки
                if self.level_select_sound:
                    arcade.play_sound(self.level_select_sound, volume=1.0)
        elif key == arcade.key.ESCAPE:
            self.window.show_view(MainMenu())


def main():
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    window.show_view(MainMenu())
    arcade.run()


if __name__ == "__main__":
    main()
