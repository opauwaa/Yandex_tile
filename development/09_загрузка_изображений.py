# добавлены изображения


import pygame
import random
import os
import sys

SCREEN_WIDTH = 500
SCREEN_HEIGHT = 800
SCREEN_COLOR = pygame.Color('white')
SCREEN_MARGIN_TOP = 100  # верхний отступ
SCREEN_MARGIN_SIDE = 50  # боковой отступ
SCREEN_MARGIN_BOTTOM = 50  # нижний отступ

BOARD_WIDTH = 5  # количество клеток в поле по ширине
BOARD_HEIGHT = 9  # количество клеток в поле по длине

#TILE_TYPE = {'0': 'orange', '1': 'powderblue', '2': 'magenta', '3': 'salmon', '4': 'turquoise'}
TILE_TYPE = {'0': 'smo.png', '1': 'ice.jpg', '2': 'burg.png', '3': 'cup.png', '4': 'gra.jpg'}
TILE_BORDER_SIZE = 5
TILE_BORDER_COLOR = 'white' #'grey40'
TILE_SELECTED_COLOR_DARK = 'white '#'grey60'
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
pygame.init()
size = width, height = SCREEN_WIDTH, SCREEN_HEIGHT
screen = pygame.display.set_mode(size)
pygame.display.set_caption('Yandex.Tile')
running = True


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
            print('это цвет')
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
            color_id = random.choice(list(TILE_TYPE.keys()))
            tl = Tile(TILE_TYPE[color_id], tile.rect.width, color_id, tile.board)
            tl.rect.x = tile.rect.x
            tl.rect.y = tile.rect.y
            tile.board.tiles.add(tl)
            #add_text('tile', tl)
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
    def __init__(self, playmap):
        # группы плиток
        self.tiles = pygame.sprite.Group()  # игровые плитки
        self.blocks = pygame.sprite.Group()  # плитки препятствий
        self.empty = pygame.sprite.Group()  # свободные плитки
        self.map = pygame.sprite.Group()  # плитки карты
        # позиция курсора над плиткой
        self.pos = None
        # считаем размеры поля
        board_width = len(playmap[0])
        board_height = len(playmap)
        h = (SCREEN_HEIGHT - SCREEN_MARGIN_TOP - SCREEN_MARGIN_BOTTOM) // board_height
        w = (SCREEN_WIDTH - SCREEN_MARGIN_SIDE * 2) // board_width
        # так как плитки квадратные
        tile_size = min(h, w)
        margin_side = (SCREEN_WIDTH - board_width * tile_size) // 2
        font = pygame.font.Font(None, int(tile_size / TILE_FONT_RATIO))
        for y in range(board_height):
            for x in range(board_width):
                if playmap[y][x] == '*':
                    # пустые клетки игнорируем
                    pass
                elif playmap[y][x] == '#':
                    # клетки препятствий
                    #tile = Tile(BLOCK_COLOR, tile_size,'-1', self)
                    tile = Tile('eda.png', tile_size, '-1', self)
                    tile.rect.x = margin_side + tile.rect.width * x
                    tile.rect.y = SCREEN_MARGIN_TOP + tile.rect.height * y
                    # расположение текста
                    #add_text('block', tile)
                    self.blocks.add(tile)
                else:
                    tile = Tile(TILE_TYPE[playmap[y][x]], tile_size,playmap[y][x], self)
                    tile.rect.x = margin_side + tile.rect.width * x
                    tile.rect.y = SCREEN_MARGIN_TOP + tile.rect.height * y
                    #add_text('tile', tile)
                    self.tiles.add(tile)

                    tile = TileEmpty(EMPTY_COLOR, tile_size,'-1', self)
                    tile.rect.x = margin_side + tile.rect.width * x
                    tile.rect.y = SCREEN_MARGIN_TOP + tile.rect.height * y
                    add_text('empty', tile)
                    self.empty.add(tile)

                    tile = Tile(MAP_COLOR, tile_size,'-1',  self)
                    tile.rect.x = margin_side + tile.rect.width * x
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
        #for i in self.tiles:
            #if not i.is_idle():
              #  return
        #for i in self.empty:
        #    if not i.is_idle():
        #        return

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


bd = Board(map_generator(BOARD_WIDTH, BOARD_HEIGHT))
while running:
    screen.fill(SCREEN_COLOR)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        bd.on_event(event)
    bd.update()
    bd.empty.update()
    bd.tiles.update()
    #bd.map.draw(screen)
    bd.blocks.draw(screen)
    #bd.empty.draw(screen)
    bd.tiles.draw(screen)
    pygame.display.flip()
pygame.quit()