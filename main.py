import pygame
import random
import json
import os
import sys

pygame.init()

SCREEN_W = 640
SCREEN_H = 480
TILE = 32
MAP_W = 10
MAP_H = 10

HUD_H = 64
MAP_OFFSET_X = (SCREEN_W - MAP_W * TILE) // 2
MAP_OFFSET_Y = HUD_H + (SCREEN_H - HUD_H - MAP_H * TILE) // 2

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (120, 120, 120)
DARK_GRAY = (60, 60, 60)
RED = (220, 40, 40)
DARK_RED = (120, 20, 20)
GREEN = (60, 200, 60)
DARK_GREEN = (30, 120, 30)
BLUE = (60, 120, 220)
YELLOW = (240, 220, 60)
GOLD = (255, 200, 40)
ORANGE = (240, 140, 40)
PURPLE = (180, 60, 200)
CYAN = (80, 200, 220)
FLOOR_COLOR = (50, 45, 40)
WALL_COLOR = (90, 80, 70)

SCORE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "highscore.json")

font_small = pygame.font.SysFont("consolas", 16)
font_medium = pygame.font.SysFont("consolas", 24)
font_large = pygame.font.SysFont("consolas", 48)
font_xlarge = pygame.font.SysFont("consolas", 72)


class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.hp = 10
        self.max_hp = 10
        self.atk = 2
        self.gold = 0
        self.floor = 1


class Monster:
    def __init__(self, kind, x, y):
        self.kind = kind
        self.x = x
        self.y = y
        if kind == "slime":
            self.hp = 3
            self.atk = 1
            self.color = GREEN
            self.label = "S"
        elif kind == "skeleton":
            self.hp = 5
            self.atk = 1
            self.color = WHITE
            self.label = "K"
        elif kind == "bat":
            self.hp = 2
            self.atk = 1
            self.color = PURPLE
            self.label = "B"
        elif kind == "boss":
            self.hp = 15
            self.atk = 3
            self.color = RED
            self.label = "!"


class Item:
    def __init__(self, kind, x, y):
        self.kind = kind
        self.x = x
        self.y = y


class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Dungeon Roguelike")
        self.clock = pygame.time.Clock()
        self.player = None
        self.monsters = []
        self.items = []
        self.tiles = []
        self.state = "playing"
        self.high_score = self.load_high_score()
        self.message = ""
        self.message_timer = 0
        self.generate_floor(1)

    def load_high_score(self):
        if os.path.exists(SCORE_FILE):
            try:
                with open(SCORE_FILE, "r") as f:
                    return json.load(f).get("high_score", 1)
            except Exception:
                return 1
        return 1

    def save_high_score(self, floor):
        if floor > self.high_score:
            self.high_score = floor
            try:
                with open(SCORE_FILE, "w") as f:
                    json.dump({"high_score": self.high_score}, f)
            except Exception:
                pass

    def generate_floor(self, floor_num):
        self.tiles = [[0] * MAP_W for _ in range(MAP_H)]
        for y in range(MAP_H):
            for x in range(MAP_W):
                self.tiles[y][x] = 1 if (x == 0 or x == MAP_W - 1 or y == 0 or y == MAP_H - 1) else 0

        extra_walls = random.randint(3, 8)
        for _ in range(extra_walls):
            wx = random.randint(1, MAP_W - 2)
            wy = random.randint(1, MAP_H - 2)
            if not (wx == 1 and wy == 1):
                self.tiles[wy][wx] = 1

        if self.player is None:
            self.player = Player(1, 1)
        else:
            self.player.x = 1
            self.player.y = 1
        self.player.floor = floor_num

        self.monsters = []
        self.items = []

        is_boss_floor = (floor_num % 3 == 0)

        if is_boss_floor:
            bx, by = self.find_empty_tile(avoid_center=True)
            self.monsters.append(Monster("boss", bx, by))
            monster_count = 1
        else:
            monster_count = random.randint(2, 4)

        for _ in range(monster_count):
            mx, my = self.find_empty_tile(avoid_center=True)
            if mx is None:
                continue
            kinds = ["slime", "skeleton", "bat"]
            if is_boss_floor:
                kinds = ["slime", "bat"]
            kind = random.choice(kinds)
            self.monsters.append(Monster(kind, mx, my))

        gold_count = random.randint(2, 5)
        for _ in range(gold_count):
            gx, gy = self.find_empty_tile(avoid_center=True)
            if gx is not None:
                self.items.append(Item("gold", gx, gy))

        potion_count = random.randint(1, 2)
        for _ in range(potion_count):
            px, py = self.find_empty_tile(avoid_center=True)
            if px is not None:
                self.items.append(Item("potion", px, py))

        self.set_message(f"Floor {floor_num} - BOSS!" if is_boss_floor else f"Floor {floor_num}")

    def find_empty_tile(self, avoid_center=False):
        tries = 0
        while tries < 200:
            x = random.randint(1, MAP_W - 2)
            y = random.randint(1, MAP_H - 2)
            if avoid_center and abs(x - 1) + abs(y - 1) < 3:
                tries += 1
                continue
            if self.tiles[y][x] != 0:
                tries += 1
                continue
            if self.player and self.player.x == x and self.player.y == y:
                tries += 1
                continue
            if any(m.x == x and m.y == y for m in self.monsters):
                tries += 1
                continue
            if any(it.x == x and it.y == y for it in self.items):
                tries += 1
                continue
            return x, y
        return None, None

    def set_message(self, msg):
        self.message = msg
        self.message_timer = 60

    def is_walkable(self, x, y):
        if x < 0 or x >= MAP_W or y < 0 or y >= MAP_H:
            return False
        return self.tiles[y][x] == 0

    def monster_at(self, x, y):
        for m in self.monsters:
            if m.x == x and m.y == y:
                return m
        return None

    def item_at(self, x, y):
        for it in self.items:
            if it.x == x and it.y == y:
                return it
        return None

    def try_move_player(self, dx, dy):
        if self.state != "playing":
            return
        nx = self.player.x + dx
        ny = self.player.y + dy
        if not self.is_walkable(nx, ny):
            return
        m = self.monster_at(nx, ny)
        if m:
            m.hp -= self.player.atk
            self.set_message(f"You hit {m.kind} for {self.player.atk}!")
            if m.hp <= 0:
                self.monsters.remove(m)
                self.set_message(f"You killed {m.kind}!")
            self.player.hp -= m.atk
            if self.player.hp <= 0:
                self.player.hp = 0
                self.state = "dead"
                self.save_high_score(self.player.floor)
            self.monsters_turn()
            return
        self.player.x = nx
        self.player.y = ny
        it = self.item_at(nx, ny)
        if it:
            self.auto_pickup(it)
        else:
            self.monsters_turn()

    def auto_pickup(self, it):
        if it.kind == "gold":
            amount = random.randint(1, 5)
            self.player.gold += amount
            self.set_message(f"Picked up {amount} gold!")
            self.items.remove(it)
        elif it.kind == "potion":
            heal = random.randint(3, 5)
            self.player.hp = min(self.player.max_hp, self.player.hp + heal)
            self.set_message(f"Drank potion +{heal} HP!")
            self.items.remove(it)

    def pickup_key(self):
        if self.state != "playing":
            return
        it = self.item_at(self.player.x, self.player.y)
        if it:
            self.auto_pickup(it)
        else:
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                it = self.item_at(self.player.x + dx, self.player.y + dy)
                if it:
                    self.auto_pickup(it)
                    return
            self.set_message("Nothing to pick up.")

    def monsters_turn(self):
        if self.player.floor >= 10:
            self.state = "win"
            self.save_high_score(self.player.floor)
            return
        for m in self.monsters[:]:
            if m not in self.monsters:
                continue
            dx = self.player.x - m.x
            dy = self.player.y - m.y
            moves = []
            if abs(dx) > abs(dy):
                if dx != 0:
                    moves.append((1 if dx > 0 else -1, 0))
                if dy != 0:
                    moves.append((0, 1 if dy > 0 else -1))
            else:
                if dy != 0:
                    moves.append((0, 1 if dy > 0 else -1))
                if dx != 0:
                    moves.append((1 if dx > 0 else -1, 0))
            moved = False
            for mx, my in moves:
                tx = m.x + mx
                ty = m.y + my
                if tx == self.player.x and ty == self.player.y:
                    self.player.hp -= m.atk
                    self.set_message(f"{m.kind} hits you for {m.atk}!")
                    if self.player.hp <= 0:
                        self.player.hp = 0
                        self.state = "dead"
                        self.save_high_score(self.player.floor)
                        return
                    moved = True
                    break
                if self.is_walkable(tx, ty) and not self.monster_at(tx, ty):
                    m.x = tx
                    m.y = ty
                    moved = True
                    break
            if not moved and m.kind == "bat":
                for mx, my in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                    tx = m.x + mx
                    ty = m.y + my
                    if self.is_walkable(tx, ty) and not self.monster_at(tx, ty) and not (tx == self.player.x and ty == self.player.y):
                        m.x = tx
                        m.y = ty
                        break
        if not self.monsters:
            self.generate_floor(self.player.floor + 1)

    def restart(self):
        self.player = None
        self.state = "playing"
        self.generate_floor(1)

    def draw_tile_rect(self, x, y, color, inset=0):
        rx = MAP_OFFSET_X + x * TILE + inset
        ry = MAP_OFFSET_Y + y * TILE + inset
        s = TILE - inset * 2
        pygame.draw.rect(self.screen, color, (rx, ry, s, s))

    def draw_text(self, text, font, color, cx, cy):
        surf = font.render(text, True, color)
        r = surf.get_rect(center=(cx, cy))
        self.screen.blit(surf, r)

    def draw(self):
        self.screen.fill(BLACK)

        pygame.draw.rect(self.screen, DARK_GRAY, (0, 0, SCREEN_W, HUD_H))
        pygame.draw.line(self.screen, GRAY, (0, HUD_H), (SCREEN_W, HUD_H), 2)

        hp_w = 200
        hp_h = 24
        hp_x = 16
        hp_y = (HUD_H - hp_h) // 2
        pygame.draw.rect(self.screen, DARK_RED, (hp_x, hp_y, hp_w, hp_h))
        hp_ratio = self.player.hp / self.player.max_hp
        pygame.draw.rect(self.screen, RED, (hp_x, hp_y, int(hp_w * hp_ratio), hp_h))
        pygame.draw.rect(self.screen, WHITE, (hp_x, hp_y, hp_w, hp_h), 2)
        self.draw_text(f"HP {self.player.hp}/{self.player.max_hp}", font_small, WHITE, hp_x + hp_w // 2, hp_y + hp_h // 2)

        self.draw_text(f"Gold: {self.player.gold}", font_medium, GOLD, SCREEN_W // 2, HUD_H // 2 - 10)
        self.draw_text(f"Floor: {self.player.floor}/10   Best: {self.high_score}", font_small, WHITE, SCREEN_W // 2, HUD_H // 2 + 14)

        self.draw_text(f"ATK {self.player.atk}", font_medium, ORANGE, SCREEN_W - 60, HUD_H // 2)

        for y in range(MAP_H):
            for x in range(MAP_W):
                if self.tiles[y][x] == 1:
                    self.draw_tile_rect(x, y, WALL_COLOR)
                else:
                    self.draw_tile_rect(x, y, FLOOR_COLOR)
                    self.draw_tile_rect(x, y, (40, 35, 30), 14)

        for it in self.items:
            if it.kind == "gold":
                cx = MAP_OFFSET_X + it.x * TILE + TILE // 2
                cy = MAP_OFFSET_Y + it.y * TILE + TILE // 2
                pygame.draw.circle(self.screen, GOLD, (cx, cy), 8)
                pygame.draw.circle(self.screen, YELLOW, (cx, cy), 5)
                self.draw_text("$", font_small, BLACK, cx, cy)
            elif it.kind == "potion":
                rx = MAP_OFFSET_X + it.x * TILE + 8
                ry = MAP_OFFSET_Y + it.y * TILE + 6
                pygame.draw.rect(self.screen, DARK_RED, (rx, ry, 16, 20))
                pygame.draw.rect(self.screen, RED, (rx + 2, ry + 4, 12, 14))
                pygame.draw.rect(self.screen, GRAY, (rx + 4, ry - 2, 8, 4))

        for m in self.monsters:
            if m.kind == "boss":
                self.draw_tile_rect(m.x, m.y, (60, 0, 0))
                self.draw_tile_rect(m.x, m.y, (140, 10, 10), 4)
                self.draw_text(m.label, font_large, WHITE, MAP_OFFSET_X + m.x * TILE + TILE // 2, MAP_OFFSET_Y + m.y * TILE + TILE // 2)
            else:
                self.draw_tile_rect(m.x, m.y, m.color, 4)
                self.draw_text(m.label, font_medium, BLACK, MAP_OFFSET_X + m.x * TILE + TILE // 2, MAP_OFFSET_Y + m.y * TILE + TILE // 2)
            if m.hp < (15 if m.kind == "boss" else (3 if m.kind == "slime" else 5 if m.kind == "skeleton" else 2)):
                bh = 4
                bw = TILE - 8
                bx = MAP_OFFSET_X + m.x * TILE + 4
                by = MAP_OFFSET_Y + m.y * TILE + 2
                maxhp = 15 if m.kind == "boss" else (3 if m.kind == "slime" else 5 if m.kind == "skeleton" else 2)
                pygame.draw.rect(self.screen, DARK_RED, (bx, by, bw, bh))
                pygame.draw.rect(self.screen, GREEN, (bx, by, int(bw * (m.hp / maxhp)), bh))

        px = MAP_OFFSET_X + self.player.x * TILE
        py = MAP_OFFSET_Y + self.player.y * TILE
        pygame.draw.rect(self.screen, BLUE, (px + 2, py + 2, TILE - 4, TILE - 4))
        pygame.draw.rect(self.screen, CYAN, (px + 6, py + 6, TILE - 12, TILE - 12))
        self.draw_text("@", font_medium, WHITE, px + TILE // 2, py + TILE // 2)

        if self.message_timer > 0:
            surf = font_medium.render(self.message, True, YELLOW)
            r = surf.get_rect(center=(SCREEN_W // 2, SCREEN_H - 24))
            pygame.draw.rect(self.screen, (0, 0, 0, 180), (r.x - 8, r.y - 4, r.w + 16, r.h + 8))
            self.screen.blit(surf, r)
            self.message_timer -= 1

        if self.state == "dead":
            overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            self.screen.blit(overlay, (0, 0))
            self.draw_text("GAME OVER", font_xlarge, RED, SCREEN_W // 2, SCREEN_H // 2 - 40)
            self.draw_text(f"Reached Floor {self.player.floor}", font_medium, WHITE, SCREEN_W // 2, SCREEN_H // 2 + 10)
            self.draw_text(f"High Score: Floor {self.high_score}", font_small, GOLD, SCREEN_W // 2, SCREEN_H // 2 + 40)
            self.draw_text("Press R to restart", font_medium, GRAY, SCREEN_W // 2, SCREEN_H // 2 + 80)

        if self.state == "win":
            overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            self.screen.blit(overlay, (0, 0))
            self.draw_text("YOU WIN!", font_xlarge, GREEN, SCREEN_W // 2, SCREEN_H // 2 - 40)
            self.draw_text(f"Gold collected: {self.player.gold}", font_medium, GOLD, SCREEN_W // 2, SCREEN_H // 2 + 10)
            self.draw_text("Press R to play again", font_medium, GRAY, SCREEN_W // 2, SCREEN_H // 2 + 60)

        pygame.display.flip()

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        if self.state in ("dead", "win"):
                            self.restart()
                    elif event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                    elif self.state == "playing":
                        if event.key in (pygame.K_LEFT, pygame.K_a):
                            self.try_move_player(-1, 0)
                        elif event.key in (pygame.K_RIGHT, pygame.K_d):
                            self.try_move_player(1, 0)
                        elif event.key in (pygame.K_UP, pygame.K_w):
                            self.try_move_player(0, -1)
                        elif event.key in (pygame.K_DOWN, pygame.K_s):
                            self.try_move_player(0, 1)
                        elif event.key == pygame.K_e:
                            self.pickup_key()
            self.draw()
            self.clock.tick(60)


if __name__ == "__main__":
    Game().run()
