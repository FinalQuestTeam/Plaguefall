"""Campaign death rules and real item/inventory effects under ASan/UBSan."""
import os
from pathlib import Path
import shlex
import subprocess
import tempfile
from test_player_aim import STUBS as PLAYER_STUBS, ROOT

STUBS = dict(PLAYER_STUBS)
STUBS['levels/campaign_factory.h'] = '#include <genesis.h>\nstatic inline bool CF_shotHit(s16 x,s16 y){(void)x;(void)y;return FALSE;}\nstatic inline void CF_bomb(void){}\n'
STUBS.pop('actors/shots.h')
STUBS['genesis.h'] = STUBS['genesis.h'].replace('#endif', '''
#include <string.h>
#include <stdlib.h>
typedef int VDPPlane;
#define PAL1 1
#define TILE_USER_INDEX 16
#define SPRITE_SIZE(w,h) ((w)*4+(h))
#define TILE_ATTR_FULL(p,a,b,c,t) (t)
u32 getApproximatedDistance(s16,s16);
u16 test_random(void);
#define random test_random
#endif''')
STUBS['core/game.h'] = '''#include <genesis.h>
#include "levels/arena.h"
extern u16 fps; extern bool gameOver; extern s16 px,py;
#define INNER_MIN_X arenaMinX
#define INNER_MIN_Y arenaMinY
#define INNER_MAX_X arenaMaxX
#define INNER_MAX_Y arenaMaxY
'''
STUBS['levels/levels.h'] = '''#ifndef LEVELS_H
#define LEVELS_H
#include <genesis.h>
#include "elements/elements.h"
typedef struct {const TileRect *lava;u16 lavaCount;u8 shotCap;} LevelDef;
extern u8 currentLevel, testStage;
const LevelDef *LEVEL_current(void);
#endif
'''
STUBS['enemies/enemies.h'] = '''#ifndef ENEMIES_H
#define ENEMIES_H
#include <genesis.h>
#define ENEMY_STATUS_FREEZE 1
#define ENEMY_STATUS_BURN 2
#define ENEMY_STATUS_NONE 0
#define ENEMY_HIT_NONE 0
#define ENEMY_HIT_KILLED 2
typedef struct {u8 dropChance;} EnemyDef;
extern const EnemyDef *const ENEMY_DEFS[];
#define MAX_ENEMIES 16
typedef struct {s16 x,y;bool active;} Enemy;
extern Enemy enemies[MAX_ENEMIES];
#define ENEMY_SIZE(e) 16
u16 ENEMIES_damageBox(s16,s16,u16,u16,u8);
u16 ENEMIES_chainDamage(s16,s16,u8,u16);
u16 ENEMIES_killAll(void);
#endif
'''
STUBS['system/audio/sfx.h'] = '''void SFX_playerHit(void);
void SFX_playerShot(void);void SFX_bombBlast(void);void sfxItemPickup(void);
'''
STUBS['system/video/herogfx.h'] += '\nvoid HERO_muzzle(s16 *,s16 *);\n'
STUBS['core/objective.h'] = '#include <genesis.h>\nvoid OBJECTIVE_addCollected(u8);\n'

TEST = (ROOT / 'game/tests/death_rules_test.c').read_text()


def main():
    compiler = shlex.split(os.environ.get('CC', 'cc'))
    src = ROOT / 'game/src'
    production = [src / name for name in ('core/death.c', 'core/inventory.c',
                  'actors/player.c', 'actors/shots_player.c', 'actors/bomb.c')]
    production += sorted((src / 'items').glob('*.c')) + sorted((src / 'items/defs').glob('*.c'))
    with tempfile.TemporaryDirectory(prefix='plaguefall-death-') as tmp:
        folder = Path(tmp)
        for name, data in STUBS.items():
            path = folder / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(data)
        (folder / 'test.c').write_text(TEST)
        binary = folder / 'death-rules'
        subprocess.run([*compiler, '-std=c99', '-Wall', '-Wextra', '-Werror',
                        '-fsanitize=address,undefined', '-I'+str(folder), '-I'+str(src),
                        str(folder / 'test.c'), *map(str, production), '-o', str(binary)], check=True)
        subprocess.run([str(binary)], check=True)


if __name__ == '__main__':
    main()
