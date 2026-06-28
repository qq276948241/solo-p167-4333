# Dungeon Roguelike 架构说明

## 这是个啥游戏？

一个纯 pygame 画方块做的回合制地牢小游戏，不用任何图片素材。玩家在 10×10 的随机地牢里走，每走一步怪物也动一下。杀怪掉剑和盾，捡金币攒分数，每 3 层一个 BOSS，闯到第 10 层就算通关。死了按 R 重开，金币和楼层保留，装备清空。

**操作**：方向键 / WASD 移动（撞怪就是攻击），E 捡脚下或旁边的东西，R 重开，ESC 退出。

---

## 文件结构

```
project167/
├── main.py          # 游戏主逻辑：输入、战斗、地图、绘制、UI
├── inventory.py     # 装备系统：背包管理、掉落判定、装备绘制
└── highscore.json   # 最高分存档（首次运行自动生成）
```

两个文件加起来约 1000 行。

---

## 核心类职责

### 1. Player — 玩家
[main.py#L47-L67](file:///d:/code/ai-prompt/solo-chrome-dev-F12/repos/repo167/project167/main.py#L47-L67)

管玩家自身的数据：
- `base_atk = 2`、`base_max_hp = 10` — 裸装基础属性
- `hp`、`max_hp`、`atk` — 当前属性（受装备加成影响）
- `gold`、`floor` — 金币数、当前楼层（死亡重开保留）
- `inventory` — 一个 `Inventory` 对象，管装备
- `equip(kind)` — 捡装备时调用，塞进背包并自动刷新属性
- `reset_equip()` — 清空装备并还原属性

### 2. Monster — 怪物
[main.py#L69-L94](file:///d:/code/ai-prompt/solo-chrome-dev-F12/repos/repo167/project167/main.py#L69-L94)

三种普通怪 + 一种 BOSS，数据全写死在构造函数里：

| 类型 | 颜色 | 标签 | HP | ATK | 掉落 |
|---|---|---|---|---|---|
| 史莱姆 slime | 绿 | S | 3 | 1 | 1/6 概率掉盾 |
| 骷髅 skeleton | 白 | K | 5 | 1 | 1/3 概率掉剑 |
| 蝙蝠 bat | 紫 | B | 2 | 1 | 啥都不掉 |
| BOSS boss | 红 | ! | 15 | 3 | 不掉 |

每个怪物存 `x, y, hp, atk, kind`。AI 很傻：看玩家在哪个方向就往哪挪一步，撞玩家就造成伤害。蝙蝠走不动时会随机晃。

### 3. Item — 地上的东西
[main.py#L96-L99](file:///d:/code/ai-prompt/solo-chrome-dev-F12/repos/repo167/project167/main.py#L96-L99)

轻量数据类，就三个字段：`kind`（gold / potion / sword / shield）+ `x` + `y`。

`sword` 和 `shield` 这两种装备类掉落，额外用 `DroppedItem`（inventory.py 里）包一层，和普通物品区分开。

### 4. Inventory — 背包（装备专用）
[inventory.py#L21-L80](file:///d:/code/ai-prompt/solo-chrome-dev-F12/repos/repo167/project167/inventory.py#L21-L80)

从 Game 类里拆出来的装备系统，只管装备：
- `slots` — 列表，最多存 2 件，超了自动顶掉最旧的
- `add(kind)` — 加装备，自动先清最旧的再塞新的（while 循环 + 最终裁剪双保险）
- `calc_atk_bonus()` / `calc_hp_bonus()` — 统计加成
- `apply_to_player(player)` — 把加成算到玩家属性上，加 HP 上限时会同步补血，降上限时不会让当前血超过新上限
- `draw_equipment(screen, px, py)` — 画玩家身上那两个装备小格子图标

### 5. ItemDrop — 掉落物工具类
[inventory.py#L82-L114](file:///d:/code/ai-prompt/solo-chrome-dev-F12/repos/repo167/project167/inventory.py#L82-L114)

全是静态方法，相当于掉落物的"工具函数集"：
- `try_drop(monster_kind, x, y, item_at_fn)` — 怪物死了调一下，按概率返回一个 `DroppedItem` 或 None
- `is_equipment(kind)` — 判断是不是装备（sword / shield）
- `draw_on_map(...)` — 画地图上的剑和盾形状

### 6. Game — 总指挥
[main.py#L103-L560](file:///d:/code/ai-prompt/solo-chrome-dev-F12/repos/repo167/project167/main.py#L103-L560)

这个类最大，把所有东西串起来。核心职责：

| 模块 | 做什么 |
|---|---|
| 地图生成 | `generate_floor()` 随机内墙、放金币血瓶、刷怪、每 3 层放 BOSS |
| 输入处理 | `run()` 主循环抓按键，转调 `try_move_player()` 或 `pickup_key()` |
| 战斗/回合 | `try_move_player()` 撞怪 → 双方扣血 → 怪物死亡判定掉落 → `monsters_turn()` 让所有怪动一次 |
| 拾取 | `check_pickup()` 统一处理金币/血瓶/装备，装备走 `player.equip()` |
| 状态机 | `state` 是 `playing` / `dead` / `win`，控制画面显示 |
| 绘制 | `draw()` 画 HUD → 画地图 → 画掉落物 → 画怪物 → 画玩家 → 画身上装备 → 画消息/GAMEOVER/YOU WIN |
| 存档 | `load_high_score()` / `save_high_score()` 读写 `highscore.json` |

---

## 玩家按方向键后的完整流程

```
玩家按 →
  ↓
run() 主循环收到 KEYDOWN 事件
  ↓
调用 try_move_player(1, 0)
  ├─ 先检查 pending_next_floor（上一层怪清完了没走），是就进下一层直接 return
  ├─ 检查下一格里有没有墙，有墙就 return
  ├─ 检查下一格里有没有怪
  │   ├─ 有怪：玩家扣怪物 ATK，怪物扣玩家 ATK
  │   │     ├─ 怪死了：从列表移除 → ItemDrop.try_drop() 按概率掉装备到地上
  │   │     └─ 然后调用 monsters_turn() 让所有剩下的怪行动
  │   └─ 没怪：玩家移动到新格子
  │         ├─ 检查新格子有没有物品，有就 check_pickup() 处理
  │         └─ 没物品也调 monsters_turn()
  └─ monsters_turn() 结束后检查：如果怪全清且 < 10 层，挂 pending_next_floor 标志
  ↓
调用 draw() 刷新画面
  ├─ 画顶部 HUD：血条、金币、楼层、攻击
  ├─ 画 10×10 方块地图
  ├─ 画地上的金币、血瓶、剑、盾
  ├─ 画怪物（带血条）
  ├─ 画玩家（蓝色方块 + @ 符号）
  └─ 画玩家右上角那两个小装备格子图标
  ↓
屏幕显示更新，等待下一次输入
```

**回合制的关键**：无论玩家移动成功/失败（撞墙不算）、攻击/拾取，只要是一次有效操作，怪物就会全体行动一次。

---

## 数据落地

### 最高分存档
文件路径由 `SCORE_FILE` 定义：[main.py#L39](file:///d:/code/ai-prompt/solo-chrome-dev-F12/repos/repo167/project167/main.py#L39)

存的是游戏同目录下的 `highscore.json`，格式很简单：
```json
{"high_score": 7}
```
- 死亡时自动存（只存最高记录）
- 启动时自动读
- 通关（到第 10 层）也会存

---

## 调参数改哪里？

所有能改的数值全是文件顶部的大写常量，直接改数字就行：

### main.py 顶部 — 画面/地图尺寸
| 常量 | 默认值 | 意思 |
|---|---|---|
| `SCREEN_W` / `SCREEN_H` | 640 / 480 | 窗口大小 |
| `TILE` | 32 | 每个方块的像素大小 |
| `MAP_W` / `MAP_H` | 10 / 10 | 地牢格子数 |
| `HUD_H` | 64 | 顶部 HUD 高度 |

### inventory.py 顶部 — 装备/掉落数值
| 常量 | 默认值 | 意思 |
|---|---|---|
| `SKELETON_SWORD_DROP` | 1/3 | 骷髅掉剑概率 |
| `SLIME_SHIELD_DROP` | 1/6 | 史莱姆掉盾概率 |
| `SWORD_ATK_BONUS` | 2 | 每把剑加几点攻击 |
| `SHIELD_HP_BONUS` | 3 | 每面盾加几点最大血量 |
| `INVENTORY_MAX` | 2 | 背包最多装几件装备 |

### 想改怪的数值？
直接改 [Monster 构造函数](file:///d:/code/ai-prompt/solo-chrome-dev-F12/repos/repo167/project167/main.py#L69-L94) 里各分支的数字。

### 想改玩家初始数值？
改 [Player 构造函数](file:///d:/code/ai-prompt/solo-chrome-dev-F12/repos/repo167/project167/main.py#L47-L58) 里的 `base_atk`、`base_max_hp`。
