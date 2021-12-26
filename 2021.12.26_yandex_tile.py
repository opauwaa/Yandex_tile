import random
import pygame

SCREEN_WIDTH = 400
SCREEN_HEIGHT = 700
TILE_FRAME_COLOR = pygame.Color('orange')
TILE_FRAME_WIDTH = 5
BOARD_WIDTH = 5
BOARD_HEIGHT = 9
BOARD_FRAME_TOP = 70
BOARD_FRAME_SIDES = 20
BOARD_FRAME_DOWN = 70
pygame.init()
size = width, height = SCREEN_WIDTH, SCREEN_HEIGHT
screen = pygame.display.set_mode(size)

class Game:
    pass

class Tile(pygame.sprite.Sprite):
    def __init__(self, size, color):
        super().__init__()
        self.image = pygame.Surface((size, size))
        self.image.fill(TILE_FRAME_COLOR)
        self.rect = self.image.get_rect()
        surf = pygame.Surface((size - TILE_FRAME_WIDTH * 2, size - TILE_FRAME_WIDTH * 2))
        surf.fill(color)
        self.image.blit(surf, (TILE_FRAME_WIDTH, TILE_FRAME_WIDTH))

tile_types = {0:'black', 1:'green', 2:'blue', 3:'purple', 4:'pink', 5:'yellow'}

class Board:
    def __init__(self, w=BOARD_WIDTH, h=BOARD_HEIGHT):
        self.map = [['*'] * w for _ in range(h)]
        self.width = w
        self.height = h
        self.tiles = pygame.sprite.Group()
        width = (SCREEN_WIDTH - BOARD_FRAME_SIDES * 2) // BOARD_WIDTH
        height = (SCREEN_HEIGHT - BOARD_FRAME_DOWN - BOARD_FRAME_TOP) // BOARD_HEIGHT
        self.tile_size = min(width, height)

        for i in self.map:
            print(i)
        for y in range(self.height):
            for x in range(self.width):
                if self.map[y][x] == '*':
                    self.map[y][x] = random.choice([1,2,3,4,5])
        print(self.map)
        for y in range(self.height):
            for x in range(self.width):
                tile = Tile(self.tile_size, pygame.Color(tile_types[self.map[y][x]]))
                tile.rect.x = (SCREEN_WIDTH - self.width * self.tile_size) // 2 + x * self.tile_size
                tile.rect.y = BOARD_FRAME_TOP + y * self.tile_size
                self.tiles.add(tile)


pygame.display.set_caption('Yandex.Tile')
screen.fill(pygame.Color('white'))
running = True
board = Board()
while running:
    screen.fill(pygame.Color('white'))
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    board.tiles.update()
    board.tiles.draw(screen)
    pygame.display.flip()
pygame.quit()
