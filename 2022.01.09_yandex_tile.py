# устранены баги падения
# реализован поиск "три в ряд"


import pygame
import random
import os
import sys
from math import cos, sin, pi
import csv

SCREEN_WIDTH = 500
SCREEN_HEIGHT = 800
SCREEN_COLOR = pygame.Color('white')
SCREEN_FONT = None
SCREEN_MARGIN_TOP = 50  # верхний отступ
SCREEN_MARGIN_SIDE = 50  # боковой отступ
SCREEN_MARGIN_BOTTOM = 100  # нижний отступ
SCREEN_TEXT_SIZE = 30
SCREEN_FONT_COLOR = 'grey60'
WELCOME_SCREEN_RULES_OFFSET = 0.7
WELCOME_SCREEN_LOGO_SIZE = 300
WELCOME_SCREEN_LOGO_OFFSET = 0.05
WELCOME_SCREEN_LEVEL_OFFSET = 4 / 6
GAME_SCREEN_BUTTON_FRAME_COLOR = 'grey60'
GAME_SCREEN_BUTTON_COLOR = 'grey70'
GAME_SCREEN_BUTTON_MARGIN = 5

BOARD_WIDTH = 5  # количество клеток в поле по ширине
BOARD_HEIGHT = 9  # количество клеток в поле по длине
BOARD_SETTING_FILE = 'setting.txt'
BOARD_LEVEL0_FILE = 'level0.txt'
BOARD_LEVEL1_FILE = 'level1.txt'

# TILE_TYPE = {'0': 'orange', '1': 'powderblue', '2': 'magenta', '3': 'salmon', '4': 'turquoise'}
# TILE_TYPE = {'0': 'cup.jpg', '1': 'ice.jpg', '2': 'burg.png', '3': 'cup.png', '4': 'chips.png', '5' : 'gra.jpg'}
TILE_BORDER_SIZE = 5
TILE_BORDER_COLOR = 'white'  # 'grey40'
TILE_SELECTED_COLOR_DARK = 'white '  # 'grey60'
TILE_SELECTED_COLOR_LIGHT = 'grey80'
TILE_FONT_COLOR = pygame.Color('tan')
TILE_FONT_RATIO = 2.6  # соотношение размера шрифта к размеру клетки
DRAG_CURSOR_PIX_THRESHOLD = 20  # порог срабатывания перетягивания плитки в пикселях
DRAG_CURSOR_XY_THRESHOLD = 0.5  # порог срабатывания перетгивания относительно отношения х к у
DRAG_SPEED = 300
DIR_DICT = {'left': (-1, 0), 'right': (1, 0), 'up': (0, -1), 'down': (0, 1)}

TILE_GEN_DELAY = 0.5  # задержка при генерации плитки
MIN_MATCHING_TILES = 3

BLOCK_COLOR = 'grey30'
EMPTY_COLOR = 'grey35'
MAP_COLOR = EMPTY_COLOR

'''
def map_generator(w, h):
    # создаем игровое поле с игровыми клетками "."
    # "*" - обозначения пустых клеток
    # "#" - обозначение клеток препятствий
    playmap = [['.'] * w for i in range(h)]
    # задаем пустые клетки и клетки препятствия
    playmap[0][3] = '*'
    playmap[3][1] = '#'
    for y in range(h):
        for x in range(w):
            if playmap[y][x] == '.':
                playmap[y][x] = str(random.choice(list(TILE_TYPE.keys())))
    return playmap
'''


def load_image(name, colorkey=None):
    fullname = os.path.join('data', name)
    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()
    image = pygame.image.load(fullname)
    if colorkey is not None:
        image = image.convert()
        if colorkey == -1:
            colorkey = image.get_at((5, 5))
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()
    return image


def add_text(txt, tile, color=TILE_FONT_COLOR, ratio=TILE_FONT_RATIO):
    font = pygame.font.Font(None, int(tile.rect.width / ratio))
    text = font.render(txt, True, color)
    text_x = (tile.rect.width - TILE_BORDER_SIZE * 2) // 2 - text.get_width() // 2
    text_y = (tile.rect.width - TILE_BORDER_SIZE * 2) // 2 - text.get_height() // 2
    tile.icon.blit(text, (text_x, text_y))
    tile.image.blit(tile.icon, (TILE_BORDER_SIZE, TILE_BORDER_SIZE))


class Tile(pygame.sprite.Sprite):
    def __init__(self, color, size, id, board, *groups):
        super().__init__(*groups)
        self.id = id
        self.board = board
        self.image = pygame.Surface((size, size))
        self.image.fill(TILE_BORDER_COLOR)
        self.rect = self.image.get_rect()
        self.icon = pygame.Surface((size - TILE_BORDER_SIZE * 2, size - TILE_BORDER_SIZE * 2))
        if color.find('.') == -1:
            if color in pygame.color.THECOLORS:
                self.icon.fill(pygame.Color(color))
            else:
                self.icon.fill(pygame.Color('red'))
                add_text(id, self, pygame.Color('white'))
        else:
            self.icon = pygame.transform.scale(load_image(color, -1), (self.icon.get_width(), self.icon.get_height()))
        self.image.blit(self.icon, (TILE_BORDER_SIZE, TILE_BORDER_SIZE))
        self.state = None

    # машина состояний плитки
    def is_idle(self):
        return self.state == None

    def do_it(self, move):
        self.state = move

    def update(self):
        if self.state:
            self.state = self.state.process(self)
            return
        # проверяем необходимость падения
        es = check_empty(self)
        if es:
            self.do_it(MoveFall(es))


# проверка пустой плитки вниз по столбцу
def check_empty(tile):
    ts = get_neighbour(tile, DIR_DICT['down'], tile.board.tiles)
    es = get_neighbour(tile, DIR_DICT['down'], tile.board.empty)
    if not ts and es and es.is_idle():
        return es
    return None


# шаблон базовой машины состояний
class Move:
    def __init__(self):
        self.state = self.start

    def process(self, tile):
        return self.state(tile)

    def start(self, tile):
        self.state = self.end
        return self

    def end(self, tile):
        return None


# машина состоний выбора клетки
class MoveSelect(Move):
    def __init__(self, color=TILE_SELECTED_COLOR_DARK):
        super().__init__()
        self.color = color

    def start(self, tile):
        tile.image.fill(self.color)
        tile.image.blit(tile.icon, (TILE_BORDER_SIZE, TILE_BORDER_SIZE))
        return None


# машина состоний отмены выбора клетки
class MoveUnselect(MoveSelect):
    def __init__(self):
        super().__init__(TILE_BORDER_COLOR)


class MoveSelectFor3Sec(Move):
    def __init__(self, color=TILE_SELECTED_COLOR_DARK):
        self.color = color
        super().__init__()

    def start(self, tile):
        tile.image.fill(self.color)
        tile.image.blit(tile.icon, (TILE_BORDER_SIZE, TILE_BORDER_SIZE))
        self.clock = pygame.time.Clock()
        self.sec_counter = 0
        self.state = self.end
        return self

    def end(self, tile):
        self.sec_counter += self.clock.tick() / 1000
        if self.sec_counter > 3:
            tile.image.fill(TILE_BORDER_COLOR)
            tile.image.blit(tile.icon, (TILE_BORDER_SIZE, TILE_BORDER_SIZE))
            return None
        return self


# поиск соседней плитки
def get_neighbour(tile, dir, group):
    center_x = tile.rect.x + tile.rect.width // 2
    center_y = tile.rect.y + tile.rect.height // 2
    for i in group:
        if i.rect.collidepoint((center_x + dir[0] * int(tile.rect.width), center_y + dir[1] * int(tile.rect.height))):
            return i
    return None


def get_shadow(tile, group):
    tl = pygame.sprite.spritecollide(tile, group, False)
    if tl:
        return tl[0]
    return None


# перетягивание с выделенеием
class MoveDragAndSelect(Move):
    def __init__(self, dir):
        self.dir = dir
        super().__init__()

    def start(self, tile):
        ts = get_neighbour(tile, self.dir, tile.board.tiles)
        if ts and ts.is_idle():
            ts.do_it(MoveSelectFor3Sec(TILE_SELECTED_COLOR_LIGHT))
            return MoveSelectFor3Sec()
        return None


# перетягивание с заменой мест
class MoveDragAndReplace(Move):
    def __init__(self, dir):
        self.dir = dir
        super().__init__()

    def start(self, tile):
        self.ts = get_neighbour(tile, self.dir, tile.board.tiles)
        if self.ts and self.ts.is_idle():
            # сохраним координаты
            self.es = get_shadow(self.ts, tile.board.empty)
            self.em = get_shadow(tile, tile.board.empty)
            self.ts.rect.x = tile.rect.x
            self.ts.rect.y = tile.rect.y
            self.dist = 0
            self.clock = pygame.time.Clock()
            self.ts.board.tiles.remove(self.ts)
            self.es.board.empty.remove(self.es)
            self.em.board.empty.remove(self.em)
            self.state = self.end
            return self
        return None

    def end(self, tile):
        self.dist += DRAG_SPEED * self.clock.tick() / 1000
        if self.dist >= tile.rect.width:
            tile.rect.x = self.ts.rect.x + tile.rect.width * self.dir[0]
            tile.rect.y = self.ts.rect.y + tile.rect.height * self.dir[1]
            self.ts.board.tiles.add(self.ts)
            self.es.board.empty.add(self.es)
            self.em.board.empty.add(self.em)
            return None
        else:
            tile.rect.x = self.ts.rect.x + self.dist * self.dir[0]
            tile.rect.y = self.ts.rect.y + self.dist * self.dir[1]
        return self


class MoveFall(Move):
    def __init__(self, es):
        self.es = es
        es.board.empty.remove(es)
        super().__init__()

    def start(self, tile):
        self.dir = DIR_DICT['down']
        self.x = tile.rect.x
        self.y = tile.rect.y
        self.dist = 0
        self.clock = pygame.time.Clock()
        self.state = self.end
        return self

    def end(self, tile):
        self.dist += DRAG_SPEED * self.clock.tick() / 1000
        if self.dist >= tile.rect.width:
            tile.rect.x = self.x + tile.rect.width * self.dir[0]
            tile.rect.y = self.y + tile.rect.height * self.dir[1]
            self.es.board.empty.add(self.es)
            return None
        else:
            tile.rect.x = self.x + self.dist * self.dir[0]
            tile.rect.y = self.y + self.dist * self.dir[1]
        return self


class MoveEmptyToTile(Move):
    def start(self, tile):
        self.clock = pygame.time.Clock()
        self.delay = 0
        self.state = self.end
        return self

    def end(self, tile):
        if pygame.sprite.spritecollideany(tile, tile.board.tiles):
            return None
        self.delay += self.clock.tick() / 1000
        if self.delay > TILE_GEN_DELAY:
            color_id = random.choice(list(tile.board.tile_types.keys()))
            tl = Tile(tile.board.tile_types[color_id], tile.rect.width, color_id, tile.board)
            tl.rect.x = tile.rect.x
            tl.rect.y = tile.rect.y
            tile.board.tiles.add(tl)
            # add_text('tile', tl)
            return None
        return self


# создаем отдельный класс для пустых клеток
class TileEmpty(Tile):
    def update(self):
        if self.state:
            self.state = self.state.process(self)
            return
        if check_new(self):
            self.do_it(MoveEmptyToTile())


def check_new(empty_tile):
    ms = get_neighbour(empty_tile, DIR_DICT['up'], empty_tile.board.map)
    if ms:
        return False
    if pygame.sprite.spritecollideany(empty_tile, empty_tile.board.tiles):
        return False
    return True


class Board:
    def __init__(self):
        fullname = os.path.join('data', BOARD_SETTING_FILE)
        if not os.path.isfile(fullname):
            print(f"Файл раскладки '{fullname}' не найден.")
            sys.exit()
        self.playmap = []
        with open(fullname, 'rt') as f:
            for line in f:
                self.playmap += [[j for j in line.rstrip('\n')]]
        # загружаем файлы уровней
        fullname = os.path.join('data', BOARD_LEVEL0_FILE)
        if not os.path.isfile(fullname):
            print(f"Файл уровня '{fullname}' не найден.")
            sys.exit()
        self.level0 = dict()
        with open(fullname, newline='\n') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            for i in reader:
                self.level0[i[0]] = i[1]
        fullname = os.path.join('data', BOARD_LEVEL1_FILE)
        if not os.path.isfile(fullname):
            print(f"Файл уровня '{fullname}' не найден.")
            sys.exit()
        self.level1 = dict()
        with open(fullname, newline='\n') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            for i in reader:
                self.level1[i[0]] = i[1]
        # считаем размеры поля
        board_width = len(self.playmap[0])
        board_height = len(self.playmap)
        h = (SCREEN_HEIGHT - SCREEN_MARGIN_TOP - SCREEN_MARGIN_BOTTOM) // board_height
        w = (SCREEN_WIDTH - SCREEN_MARGIN_SIDE * 2) // board_width
        # так как плитки квадратные
        self.tile_size = min(h, w)
        self.margin_side = (SCREEN_WIDTH - board_width * self.tile_size) // 2
        self.size = (self.tile_size * board_width, self.tile_size * board_height)
        self.score = 0

    def set_level(self, n):
        self.tile_types = self.level0
        if n == BOARD_LEVEL1_FILE:
            self.tile_types = self.level1
        for y in range(len(self.playmap)):
            for x in range(len(self.playmap[0])):
                if self.playmap[y][x] == '.':
                    self.playmap[y][x] = random.choice(list(self.tile_types.keys()))

    def render(self):
        # группы плиток
        self.tiles = pygame.sprite.Group()  # игровые плитки
        self.blocks = pygame.sprite.Group()  # плитки препятствий
        self.empty = pygame.sprite.Group()  # свободные плитки
        self.map = pygame.sprite.Group()  # плитки карты
        # позиция курсора над плиткой
        self.pos = None
        self.state = None
        board_width = len(self.playmap[0])
        board_height = len(self.playmap)
        font = pygame.font.Font(None, int(self.tile_size / TILE_FONT_RATIO))
        for y in range(board_height):
            for x in range(board_width):
                if self.playmap[y][x] == '*':
                    # пустые клетки игнорируем
                    pass
                elif self.playmap[y][x] == '#':
                    # клетки препятствий
                    # tile = Tile(BLOCK_COLOR, tile_size,'-1', self)
                    tile = Tile('eda.png', self.tile_size, '-1', self)
                    tile.rect.x = self.margin_side + tile.rect.width * x
                    tile.rect.y = SCREEN_MARGIN_TOP + tile.rect.height * y
                    # расположение текста
                    # add_text('block', tile)
                    self.blocks.add(tile)
                else:
                    tile = Tile(self.tile_types[self.playmap[y][x]], self.tile_size, self.playmap[y][x], self)
                    tile.rect.x = self.margin_side + tile.rect.width * x
                    tile.rect.y = SCREEN_MARGIN_TOP + tile.rect.height * y
                    # add_text('tile', tile)
                    self.tiles.add(tile)

                    tile = TileEmpty(EMPTY_COLOR, self.tile_size, '-1', self)
                    tile.rect.x = self.margin_side + tile.rect.width * x
                    tile.rect.y = SCREEN_MARGIN_TOP + tile.rect.height * y
                    add_text('empty', tile)
                    self.empty.add(tile)

                    tile = Tile(MAP_COLOR, self.tile_size, '-1', self)
                    tile.rect.x = self.margin_side + tile.rect.width * x
                    tile.rect.y = SCREEN_MARGIN_TOP + tile.rect.height * y
                    add_text('map', tile)
                    self.map.add(tile)

    def on_event(self, event):
        # стирает игровую плитку при нажатии правой клавиши мыши
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            for i in self.tiles:
                if i.rect.collidepoint(event.pos) and i.is_idle():
                    i.board.tiles.remove(i)
            return
        # перетаскивание игровой плитки левой клавишей
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i in self.tiles:
                if i.rect.collidepoint(event.pos):
                    self.pos = event.pos
                    return
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.pos = None
            return
        # обработка перетаскивания
        dir = [0, 0]
        if event.type == pygame.MOUSEMOTION:
            if self.pos == None:
                return
            dx = abs(event.pos[0] - self.pos[0])
            dy = abs(event.pos[1] - self.pos[1])

            if max(dx, dy) < DRAG_CURSOR_PIX_THRESHOLD:
                return

            if dx >= dy and (dy / dx) < DRAG_CURSOR_XY_THRESHOLD:
                dir[0] = int((event.pos[0] - self.pos[0]) / dx)

            elif dy > dx and (dx / dy) < DRAG_CURSOR_XY_THRESHOLD:
                dir[1] = int((event.pos[1] - self.pos[1]) / dy)
            else:
                self.pos = None
                return

            for i in self.tiles:
                if i.rect.collidepoint(self.pos) and i.is_idle():
                    # i.do_it(MoveDragAndSelect(dir))
                    i.do_it(MoveDragAndReplace(dir))

    def update(self):
        def check_three(tile, dir):
            if not tile.is_idle():
                return []
            if dir == DIR_DICT['down']:
                ts = get_neighbour(tile, DIR_DICT['up'], tile.board.tiles)
            else:
                ts = get_neighbour(tile, DIR_DICT['left'], tile.board.tiles)
            if ts:
                if ts.id == tile.id:
                    return []
            tiles = [tile]
            while True:
                ts = get_neighbour(tiles[-1], dir, tile.board.tiles)
                if not ts or not ts.is_idle() or ts.id != tile.id:
                    break
                td = get_neighbour(ts, DIR_DICT['down'], tile.board.tiles)
                ed = get_neighbour(ts, DIR_DICT['down'], tile.board.empty)
                if not td and ed:
                    break

                tiles += [ts]
            if len(tiles) < MIN_MATCHING_TILES:
                return []
            return tiles

        tiles = []
        for i in self.tiles:
            tiles += check_three(i, DIR_DICT['down'])
            tiles += check_three(i, DIR_DICT['right'])
        self.tiles.remove(set(tiles))
        self.score += len(set(tiles))


class GuiElement(Tile):
    def __init__(self, *groups):
        pygame.sprite.Sprite.__init__(self, *groups)
        self.state = None

    def update(self):
        if self.state:
            self.state = self.state.process(self)


class GuiLabel(GuiElement):
    def __init__(self, txt, x, y, color, size, *groups):
        super().__init__(*groups)
        self.text = txt
        font = pygame.font.Font(SCREEN_FONT, size)
        t = font.render(txt, True, color)
        self.image = pygame.Surface((t.get_width(), t.get_height()))
        self.image.fill(SCREEN_COLOR)
        self.rect = pygame.Rect(x, y, t.get_width(), t.get_height())
        self.image.blit(t, (0, 0))


def draw_spiral(a, b, tile, delta=pi / 4, step=0.01, loops=3):
    def polar_to_cartesian(r, theta):
        return int(r * cos(theta)), int(r * sin(theta))

    def translate(point, tile_size):
        return point[0] + tile_size / 2, point[1] + tile_size / 2

    thickness = a // 12
    # delta=pi/4
    theta = 0.0
    a = a - thickness
    r = a
    while theta + delta < 2 * loops * pi + delta:
        theta += step
        r = a + b * theta
        # Draw pixels, but remember to convert to Cartesian:
        pos = polar_to_cartesian(r, theta + delta)
        pygame.draw.circle(tile.image, pygame.Color('orange'), translate(pos, tile.rect.width), thickness)
    pos1 = polar_to_cartesian(a - thickness * 2, delta)
    pos2 = polar_to_cartesian(a + thickness * 2, delta)
    pygame.draw.line(tile.image, pygame.Color(SCREEN_COLOR),
                     translate(pos1, tile.rect.width),
                     translate(pos2, tile.rect.width), int(thickness * 2.5))


class GuiLogo(GuiElement):
    def __init__(self, size, x, y, *groups):
        super().__init__(*groups)
        self.image = pygame.Surface((size, size))
        self.image.fill(pygame.Color(SCREEN_COLOR))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        draw_spiral(size // 2, - size // 40, self)
        self.state = MoveGuiLogo()


class MoveGuiLogo(Move):
    def start(self, tile):
        self.clock = pygame.time.Clock()
        self.sec_counter = 0
        self.delta = pi / 4
        self.state = self.end
        return self

    def end(self, tile):
        self.sec_counter += self.clock.tick() / 1000
        if self.sec_counter > 0.05:
            self.delta += 0.05
            tile.image.fill(pygame.Color(SCREEN_COLOR))
            draw_spiral(tile.rect.width // 2, -tile.rect.width // 40, tile, self.delta)
            self.sec_counter = 0
        return self

class GuiButton(GuiElement):
    def __init__(self, txt, radius, x, y, color, ratio, *groups):
        super().__init__(*groups)
        self.text = txt
        self.image = pygame.Surface((2 * radius, 2 * radius))
        self.image.fill(pygame.Color(SCREEN_COLOR))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        pygame.draw.circle(self.image, pygame.Color(GAME_SCREEN_BUTTON_FRAME_COLOR), (radius, radius), radius)
        pygame.draw.circle(self.image, pygame.Color(GAME_SCREEN_BUTTON_COLOR),
                           (radius, radius), radius - GAME_SCREEN_BUTTON_MARGIN)
        font = pygame.font.Font(SCREEN_FONT, int(self.rect.width / ratio))
        text = font.render(txt, True, color)
        text_x = self.rect.width // 2 - text.get_width() // 2
        text_y = self.rect.height // 2 - text.get_height() // 2

        self.image.blit(text, (text_x, text_y))

# класс пользовательского интерфейса
class Game:
    def welcome(self, screen, board):
        # элементы окна приветствия
        self.ww_elements = pygame.sprite.Group()
        self.ww_level0 = pygame.sprite.Group()
        self.ww_level1 = pygame.sprite.Group()
        label = GuiLabel('Выберите меню и начните набирать скидку', 0,
                         int(screen.get_height() * WELCOME_SCREEN_RULES_OFFSET),
                         pygame.Color(SCREEN_FONT_COLOR), SCREEN_TEXT_SIZE, self.ww_elements)
        label.rect.x = screen.get_width() // 2 - label.rect.width // 2
        label = GuiLabel('до приезда курьера.', 0,
                         int(screen.get_height() * WELCOME_SCREEN_RULES_OFFSET + SCREEN_TEXT_SIZE),
                         pygame.Color(SCREEN_FONT_COLOR), SCREEN_TEXT_SIZE, self.ww_elements)
        label.rect.x = screen.get_width() // 2 - label.rect.width // 2
        label = GuiLabel('Левая клавиша мыши переставляет блюда.', 0,
                         int(screen.get_height() * WELCOME_SCREEN_RULES_OFFSET + SCREEN_TEXT_SIZE * 2),
                         pygame.Color(SCREEN_FONT_COLOR), SCREEN_TEXT_SIZE, self.ww_elements)
        label.rect.x = screen.get_width() // 2 - label.rect.width // 2
        label = GuiLabel('Правая - стирает.', 0,
                         int(screen.get_height() * WELCOME_SCREEN_RULES_OFFSET + SCREEN_TEXT_SIZE * 3),
                         pygame.Color(SCREEN_FONT_COLOR), SCREEN_TEXT_SIZE, self.ww_elements)
        label.rect.x = screen.get_width() // 2 - label.rect.width // 2
        label = GuiLabel('При получении комбинации из 3 и более', 0,
                         int(screen.get_height() * WELCOME_SCREEN_RULES_OFFSET + SCREEN_TEXT_SIZE * 4),
                         pygame.Color(SCREEN_FONT_COLOR), SCREEN_TEXT_SIZE, self.ww_elements)
        label.rect.x = screen.get_width() // 2 - label.rect.width // 2
        label = GuiLabel('блюд в ряд Вам добавится скидка.', 0,
                         int(screen.get_height() * WELCOME_SCREEN_RULES_OFFSET + SCREEN_TEXT_SIZE * 5),
                         pygame.Color(SCREEN_FONT_COLOR), SCREEN_TEXT_SIZE, self.ww_elements)
        label.rect.x = screen.get_width() // 2 - label.rect.width // 2

        # рисуем лого
        logo = GuiLogo(WELCOME_SCREEN_LOGO_SIZE, 0, 0, self.ww_elements)
        logo.rect.x = screen.get_width() // 2 - logo.rect.width // 2
        logo.rect.y = screen.get_height() * WELCOME_SCREEN_LOGO_OFFSET

        # создаем выбор меню
        type = random.choice(list(board.level0.keys()))
        tile = Tile(board.level0[type], board.tile_size, type, board, self.ww_level0)
        tile.rect.x = screen.get_width() // 4 - tile.rect.width // 2
        tile.rect.y = screen.get_height() * 0.5

        type = random.choice(list(board.level1.keys()))
        tile = Tile(board.level1[type], board.tile_size, type, board, self.ww_level1)
        tile.rect.x = 3 * screen.get_width() // 4 - tile.rect.width // 2
        tile.rect.y = screen.get_height() * 0.5
        running = True
        while running:
            screen.fill(SCREEN_COLOR)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for i in self.ww_level0:
                        if i.rect.collidepoint(event.pos):
                            board.set_level(BOARD_LEVEL0_FILE)
                            return
                    for i in self.ww_level1:
                        if i.rect.collidepoint(event.pos):
                            board.set_level(BOARD_LEVEL1_FILE)
                            return
            self.ww_elements.update()
            self.ww_elements.draw(screen)
            self.ww_level0.draw(screen)
            self.ww_level1.draw(screen)
            pygame.display.flip()

    def game(self, screen, board):
        self.gw_elements = pygame.sprite.Group()
        self.guiscore = GuiLabel('СКИДКА:', 5, 5, pygame.Color(SCREEN_FONT_COLOR), SCREEN_TEXT_SIZE, self.gw_elements)
        self.guitimer = GuiLabel('00:00', 0, 5, pygame.Color(SCREEN_FONT_COLOR), SCREEN_TEXT_SIZE, self.gw_elements)
        self.guitimer.rect.x = screen.get_width() - self.guitimer.rect.width - 5
        r = SCREEN_MARGIN_BOTTOM // 2 - 3
        y = screen.get_height() - SCREEN_MARGIN_BOTTOM
        x = screen.get_width() // 2 - r
        self.guistop = GuiButton('Стоп', r, x, y, pygame.Color(SCREEN_FONT_COLOR), 2.5, self.gw_elements)
        running = True
        bd.render()
        t = pygame.time.Clock()
        self.min = '0'
        self.sec = '0'
        t_interval = 0
        while running:
            t_interval += t.tick() / 1000
            if t_interval >= 60 * 60:
                t_interval = 0
            self.min = f'{t_interval // 60:02.0f}'
            self.sec = f'{t_interval % 60:02.0f}'
            screen.fill(SCREEN_COLOR)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.guistop.rect.collidepoint(event.pos):
                        return
                bd.on_event(event)
            bd.update()
            self.game_update(screen, board)
            bd.empty.update()
            bd.tiles.update()
            # bd.map.draw(screen)
            bd.blocks.draw(screen)
            self.gw_elements.draw(screen)
            # bd.empty.draw(screen)
            bd.tiles.draw(screen)
            pygame.display.flip()

    def game_update(self, screen, board):
        self.gw_elements.remove(self.guiscore)
        self.guiscore = GuiLabel(f'СКИДКА: {board.score / 1000}%', 5, 5,
                                 pygame.Color(SCREEN_FONT_COLOR), SCREEN_TEXT_SIZE, self.gw_elements)
        self.gw_elements.remove(self.guitimer)
        self.guitimer = GuiLabel(f'{self.min}:{self.sec}', 0, 5, pygame.Color(SCREEN_FONT_COLOR),
                                 SCREEN_TEXT_SIZE, self.gw_elements)
        self.guitimer.rect.x = screen.get_width() - self.guitimer.rect.width - 5


    def farewell(self, screen, board):
        self.fw_elements = pygame.sprite.Group()
        y = screen.get_height() // 3
        label =  GuiLabel('Ваша скидка составила', 0, y, pygame.Color(SCREEN_FONT_COLOR), SCREEN_TEXT_SIZE, self.fw_elements)
        label.rect.x = screen.get_width() // 2  - label.rect.width // 2
        self.guidiscount =  GuiLabel(f'{board.score / 1000}%', 0, y + SCREEN_TEXT_SIZE, pygame.Color(SCREEN_FONT_COLOR), SCREEN_TEXT_SIZE, self.fw_elements)
        self.guidiscount.rect.x = screen.get_width() // 2 - self.guidiscount.rect.width // 2
        r = SCREEN_MARGIN_BOTTOM // 2 - 3
        y = screen.get_height() - SCREEN_MARGIN_BOTTOM
        x = screen.get_width() // 2 - r
        self.guiexit = GuiButton('Выйти', r, x, y, pygame.Color(SCREEN_FONT_COLOR), 2.5, self.fw_elements)
        running = True
        while running:
            screen.fill(SCREEN_COLOR)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.guiexit.rect.collidepoint(event.pos):
                        return
            self.fw_elements.draw(screen)
            pygame.display.flip()

bd = Board()
pygame.init()
size = width, height = SCREEN_WIDTH, SCREEN_HEIGHT
screen = pygame.display.set_mode(size)
pygame.display.set_caption('Yandex.Tile')
g = Game()
g.welcome(screen, bd)
g.game(screen, bd)
g.farewell(screen, bd)
pygame.quit()