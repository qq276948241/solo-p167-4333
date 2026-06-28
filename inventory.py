import random
import pygame

SKELETON_SWORD_DROP = 1 / 3
SLIME_SHIELD_DROP = 1 / 6
SWORD_ATK_BONUS = 2
SHIELD_HP_BONUS = 3
INVENTORY_MAX = 2

SWORD_COLOR = (120, 120, 120)
SHIELD_COLOR = (140, 90, 50)
SWORD_BLADE_COLOR = (255, 255, 255)
SWORD_GUARD_COLOR = (60, 60, 60)
SHIELD_INNER_COLOR = (200, 160, 100)
SHIELD_DARK_COLOR = (100, 60, 30)
SLOT_BORDER_COLOR = (0, 0, 0)

EQUIP_KINDS = {"sword", "shield"}


class Inventory:
    def __init__(self):
        self.slots = []

    def add(self, kind):
        if kind not in EQUIP_KINDS:
            return
        if len(self.slots) >= INVENTORY_MAX:
            self.slots.pop(0)
        self.slots.append(kind)

    def clear(self):
        self.slots.clear()

    def calc_atk_bonus(self):
        return sum(SWORD_ATK_BONUS for eq in self.slots if eq == "sword")

    def calc_hp_bonus(self):
        return sum(SHIELD_HP_BONUS for eq in self.slots if eq == "shield")

    def apply_to_player(self, player):
        player.atk = player.base_atk + self.calc_atk_bonus()
        old_max = player.max_hp
        player.max_hp = player.base_max_hp + self.calc_hp_bonus()
        if player.max_hp > old_max:
            player.hp += player.max_hp - old_max
        else:
            player.hp = min(player.hp, player.max_hp)

    def draw_equipment(self, screen, px, py):
        slot_w = 14
        slot_h = 14
        for i, eq in enumerate(self.slots):
            sx = px - 4
            sy = py - 2 + i * (slot_h + 2)
            color = SWORD_COLOR if eq == "sword" else SHIELD_COLOR
            pygame.draw.rect(screen, SLOT_BORDER_COLOR, (sx - 1, sy - 1, slot_w + 2, slot_h + 2))
            pygame.draw.rect(screen, color, (sx, sy, slot_w, slot_h))
            if eq == "sword":
                pygame.draw.rect(screen, SWORD_BLADE_COLOR, (sx + slot_w // 2 - 1, sy + 2, 2, slot_h - 5))
                pygame.draw.rect(screen, SWORD_GUARD_COLOR, (sx + 2, sy + slot_h - 5, slot_w - 4, 2))
            else:
                pygame.draw.polygon(screen, SHIELD_INNER_COLOR, [
                    (sx + 3, sy + 3), (sx + slot_w - 3, sy + 3),
                    (sx + slot_w - 3, sy + 7), (sx + slot_w // 2, sy + slot_h - 2),
                    (sx + 3, sy + 7)
                ])


class ItemDrop:
    @staticmethod
    def try_drop(monster_kind, x, y, item_at_fn):
        if monster_kind == "skeleton" and random.random() < SKELETON_SWORD_DROP:
            if not item_at_fn(x, y):
                return DroppedItem("sword", x, y)
        elif monster_kind == "slime" and random.random() < SLIME_SHIELD_DROP:
            if not item_at_fn(x, y):
                return DroppedItem("shield", x, y)
        return None

    @staticmethod
    def is_equipment(kind):
        return kind in EQUIP_KINDS

    @staticmethod
    def draw_on_map(screen, item, offset_x, offset_y, tile_size, draw_text_fn, font_small):
        bx = offset_x + item.x * tile_size + tile_size // 2
        by = offset_y + item.y * tile_size + tile_size // 2
        if item.kind == "sword":
            pygame.draw.rect(screen, SWORD_COLOR, (bx - 2, by - 12, 4, 20))
            pygame.draw.rect(screen, SWORD_GUARD_COLOR, (bx - 8, by + 6, 16, 3))
            pygame.draw.rect(screen, SHIELD_COLOR, (bx - 3, by + 9, 6, 5))
        elif item.kind == "shield":
            pygame.draw.polygon(screen, SHIELD_COLOR, [
                (bx - 9, by - 10), (bx + 9, by - 10),
                (bx + 9, by + 2), (bx, by + 12), (bx - 9, by + 2)
            ])
            pygame.draw.polygon(screen, SHIELD_DARK_COLOR, [
                (bx - 6, by - 7), (bx + 6, by - 7),
                (bx + 6, by), (bx, by + 8), (bx - 6, by)
            ])


class DroppedItem:
    def __init__(self, kind, x, y):
        self.kind = kind
        self.x = x
        self.y = y
