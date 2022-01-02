# реализована фактическая функция перетягивания плитки
# при нажатой левой клавише мыши
# при нажатии правой клавиши мыши с поля полностью убирается игровая плитка


import pygame
import random

SCREEN_WIDTH = 400
SCREEN_HEIGHT = 700
SCREEN_COLOR = pygame.Color('white')
SCREEN_MARGIN_TOP = 100  # верхний отступ
SCREEN_MARGIN_SIDE = 50  # боковой отступ
SCREEN_MARGIN_BOTTOM = 50  # нижний отступ

BOARD_WIDTH = 5  # количество клеток в поле по ширине
BOARD_HEIGHT = 9  # количество клеток в поле по длине

TILE_TYPE = {0: 'orange', 1: 'powderblue', 2: 'magenta', 3: 'salmon', 4: 'turquoise'}
TILE_BORDER_SIZE = 5
TILE_BORDER_COLOR = 'white'
TILE_SELECTED_COLOR_DARK = 'grey60'
TILE_SELECTED_COLOR_LIGHT = 'grey80'
TILE_FONT_COLOR = pygame.Color('tan')
TILE_FONT_RATIO = 2.6  # соотношение размера шрифта к размеру клетки
DRAG_CURSOR_PIX_THRESHOLD = 20  # порог срабатывания перетягивания плитки в пикселях
DRAG_CURSOR_XY_THRESHOLD = 0.5  # порог срабатывания перетгивания относительно отношения х к у
DRAG_SPEED = 50

BLOCK_COLOR = (50, 50, 50)
EMPTY_COLOR = (200, 200, 200)
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


class Tile(pygame.sprite.Sprite):
    def __init__(self, color, size, board, *groups):
        super().__init__(*groups)
        self.id = -1
        self.board = board
        self.image = pygame.Surface((size, size))
        self.image.fill(TILE_BORDER_COLOR)
        self.icon = pygame.Surface((size - TILE_BORDER_SIZE * 2, size - TILE_BORDER_SIZE * 2))
        self.icon.fill(color)
        self.image.blit(self.icon, (TILE_BORDER_SIZE, TILE_BORDER_SIZE))
        self.rect = self.image.get_rect()
        self.state = None

    # машина состояний плитки
    def is_idle(self):
        return self.state == None

    def do_it(self, move):
        self.state = move

    def update(self):
        if self.state:
            self.state = self.state.process(self)


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


# первая машина
class MoveFirst(Move):
    def start(self, tile):
        print('старт')
        self.state = self.end
        return self

    def end(self, tile):
        print('конец')
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
        if i.rect.collidepoint((center_x + dir[0] * tile.rect.width, center_y + dir[1] * tile.rect.height)):
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


def add_text(txt, tile):
    font = pygame.font.Font(None, int(tile.rect.width / TILE_FONT_RATIO))
    text = font.render(txt, True, TILE_FONT_COLOR)
    text_x = (tile.rect.width - TILE_BORDER_SIZE * 2) // 2 - text.get_width() // 2
    text_y = (tile.rect.width - TILE_BORDER_SIZE * 2) // 2 - text.get_height() // 2
    tile.icon.blit(text, (text_x, text_y))
    tile.image.blit(tile.icon, (TILE_BORDER_SIZE, TILE_BORDER_SIZE))


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
                    tile = Tile(BLOCK_COLOR, tile_size, self)
                    tile.rect.x = margin_side + tile.rect.width * x
                    tile.rect.y = SCREEN_MARGIN_TOP + tile.rect.height * y
                    # расположение текста
                    add_text('block', tile)
                    self.blocks.add(tile)
                else:
                    tile = Tile(pygame.Color(TILE_TYPE[int(playmap[y][x])]), tile_size, self)
                    tile.rect.x = margin_side + tile.rect.width * x
                    tile.rect.y = SCREEN_MARGIN_TOP + tile.rect.height * y
                    add_text('tile', tile)
                    tile.id = int(playmap[y][x])
                    self.tiles.add(tile)

                    tile = Tile(EMPTY_COLOR, tile_size, self)
                    tile.rect.x = margin_side + tile.rect.width * x
                    tile.rect.y = SCREEN_MARGIN_TOP + tile.rect.height * y
                    add_text('empty', tile)
                    self.empty.add(tile)

                    tile = Tile(MAP_COLOR, tile_size, self)
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


bd = Board(map_generator(BOARD_WIDTH, BOARD_HEIGHT))
while running:
    screen.fill(SCREEN_COLOR)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        bd.on_event(event)
    bd.tiles.update()
    # bd.map.draw(screen)
    bd.blocks.draw(screen)
    bd.empty.draw(screen)
    bd.tiles.draw(screen)
    pygame.display.flip()
pygame.quit()
