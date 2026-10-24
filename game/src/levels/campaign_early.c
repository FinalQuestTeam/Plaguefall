// Complete modular worlds authored by art/campaign-pattern-v2/early/build_scenes.py.
#include "levels/campaign_early.h"
#include "levels/graph.h"
#include "core/campaign_state.h"
#include "campaign_early_church_ruins.inc"
#include "campaign_early_street.inc"
#include "campaign_early_depot.inc"
#include "campaign_early_signal.inc"
#include "campaign_early_signal_npc.inc"

static const ArenaScene ruinsScene={
    .tiles=church_ruins_tiles,.map=church_ruins_map,.damaged=church_ruins_map,
    .palette=church_ruins_palette,.tileCount=sizeof(church_ruins_tiles)/32,
    .rows=48,.cols=64
};
// Whole bomb rubble and courtyard belongings retain their visible contact areas.
static const ArenaRect ruinsSolids[]={
    {88,184,72,40,FALSE},
    {136,288,72,40,FALSE},
    {392,264,40,40,FALSE},
    {168,152,56,32,FALSE},
    {280,216,56,32,FALSE},
    {72,248,56,32,FALSE}
};
const ArenaDef EARLY_ARENA02B={
    512,384,24,128,487,351,256,160,
    ruinsSolids,sizeof(ruinsSolids)/sizeof(ruinsSolids[0]),&ruinsScene
};
static ArenaScene streetScene={
    .tiles=street_tiles,.map=street_map,.palette=street_palette,
    .tileCount=sizeof(street_tiles)/32,.rows=40,.cols=320,.cameraPlayerY=200,.cameraFocus=streetCameraFocus,.cameraFocusCount=6
};
#include "campaign_early_street_layout.inc"
void EARLY_prepare(u8 node)
{
    if(node==N_3) {
        const bool ruined=campaignFlags&CAMPAIGN_CHURCH_RUINED;
        streetScene.map=ruined ? street_damaged_map : street_map;
        streetScene.tiles=ruined ? street_damaged_tiles : street_tiles;
        streetScene.tileCount=ruined ? sizeof(street_damaged_tiles)/32 : sizeof(street_tiles)/32;
    }
}
static const ArenaScene depotScene={
    .tiles=depot_tiles,.map=depot_map,.palette=depot_palette,
    .tileCount=sizeof(depot_tiles)/32,.rows=40,.cols=64
};
static const ArenaRect depotSolids[]={
    {64,120,96,48,TRUE},
    {336,168,96,48,TRUE},
    {208,208,64,48,TRUE}
};
const ArenaDef EARLY_ARENA04={
    512,320,32,104,479,263,48,112,
    depotSolids,sizeof(depotSolids)/sizeof(depotSolids[0]),&depotScene
};
// Preserve Santa's native floor restoration, contact footprint and crown flash.
static const ArenaNpcVisual signalNpc={
    22,20,5,8,earlyNpcFloor,{176,176,40,48,FALSE},194,181,EARLY_NPC_CROWN,112
};
static const ArenaScene signalScene={
    .tiles=signal_tiles,.map=signal_map,.damaged=signal_map,.palette=signal_palette,
    .tileCount=sizeof(signal_tiles)/32,.rows=40,.cols=48,
    .npcInMap=TRUE,.npcVisual=&signalNpc
};
static const ArenaRect signalSolids[]={
    {176,176,40,48,FALSE},
    {40,144,56,40,TRUE},
    {304,224,40,40,FALSE}
};
const ArenaDef EARLY_ARENA05={
    384,320,16,112,367,271,64,232,
    signalSolids,sizeof(signalSolids)/sizeof(signalSolids[0]),&signalScene
};
