# добавлена функция снятия выбора клетки через 3 секунды после нажатия
# реализовано с помощью машины состояний


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

TILE_TYPE = {0: 'orange', 1: 'brown', 2: 'magenta', 3: 'yellow', 4: 'turquoise'}
TILE_BORDER_SIZE = 5
TILE_BORDER_COLOR = (80, 80, 80)
TILE_SELECTED_COLOR_DARK = (150, 150, 150)
TILE_SELECTED_COLOR_LIGHT = (200, 200, 200)

BLOCK_COLOR = (50, 50, 50)
PLAYGROUND_COLOR = (200, 200, 200)
pygame.init()
size = width, height = SCREEN_WIDTH, SCREEN_HEIGHT
screen = pygame.display.set_mode(size)
pygame.display.set_caption('Yandex.Tile')
running = True


def map_generate(w, h):
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


class Board:
    def __init__(self, playmap):
        # группы плиток
        self.tiles = pygame.sprite.Group()
        self.blocks = pygame.sprite.Group()
        self.playground = pygame.sprite.Group()
        # позиция курсора над плиткой
        self.pos = (-1, -1)
        # считаем размеры поля
        board_width = len(playmap[0])
        board_height = len(playmap)
        h = (SCREEN_HEIGHT - SCREEN_MARGIN_TOP - SCREEN_MARGIN_BOTTOM) // board_height
        w = (SCREEN_WIDTH - SCREEN_MARGIN_SIDE * 2) // board_width
        # так как плитки квадратные
        self.tile_size = min(h, w)
        margin_side = (SCREEN_WIDTH - board_width * self.tile_size) // 2
        for y in range(board_height):
            for x in range(board_width):
                if playmap[y][x] == '*':
                    # пустые клетки игнорируем
                    pass
                elif playmap[y][x] == '#':
                    # клетки препятствий
                    tile = Tile(BLOCK_COLOR, self.tile_size, self)
                    tile.rect.x = margin_side + self.tile_size * x
                    tile.rect.y = SCREEN_MARGIN_TOP + self.tile_size * y
                    self.blocks.add(tile)
                else:
                    tile = Tile(pygame.Color(TILE_TYPE[int(playmap[y][x])]), self.tile_size, self)
                    tile.rect.x = margin_side + self.tile_size * x
                    tile.rect.y = SCREEN_MARGIN_TOP + self.tile_size * y
                    tile.id = int(playmap[y][x])
                    self.tiles.add(tile)
                    tile = Tile(PLAYGROUND_COLOR, self.tile_size, self)
                    tile.rect.x = margin_side + self.tile_size * x
                    tile.rect.y = SCREEN_MARGIN_TOP + self.tile_size * y
                    self.playground.add(tile)

    def get_click(self, pos):
        for i in self.tiles:
            if i.rect.collidepoint(pos):
                self.pos = pos
                i.do_it(MoveSelectFor3Sec())


bd = Board(map_generate(BOARD_WIDTH, BOARD_HEIGHT))
while running:
    screen.fill(SCREEN_COLOR)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            bd.get_click(event.pos)
    bd.tiles.update()
    bd.blocks.draw(screen)
    bd.playground.draw(screen)
    bd.tiles.draw(screen)
    pygame.display.flip()
pygame.quit()
