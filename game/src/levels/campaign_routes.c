// Exact native corridor export.
#include "levels/campaign_routes.h"
#include <campaign_routes.h>
static const ArenaRect cameraFocus06a[]={{56,24,102,144,FALSE},{2880,24,128,115,FALSE}};

static const ArenaStream stream06a={1095};
static const ArenaScene scene06a={.tiles=(const u32 *)campaign_route06a_tiles,.map=(const u16 *)campaign_route06a_map,.palette=(const u16 *)campaign_route06a_palette,.tileCount=456,.rows=40,.cols=384,.cameraPlayerY=200,.cameraFocus=cameraFocus06a,.cameraFocusCount=2,.stream=&stream06a,.streamOverlay=TRUE,.cameraSouthStart=192};
static const ArenaRect solids06a[]={{56,80,104,88,TRUE},{2880,80,128,64,TRUE},{320,224,32,16,TRUE},{656,112,80,48,TRUE},{880,240,32,16,TRUE},{1168,248,48,16,FALSE},{1376,128,32,16,TRUE},{1672,112,80,48,TRUE},{1968,248,48,16,FALSE},{2184,240,32,16,TRUE},{2368,128,40,24,FALSE},{832,80,32,32,TRUE},{832,176,32,96,TRUE},{1856,80,32,112,TRUE},{1856,256,32,16,TRUE}};

const ArenaDef CAMPAIGN_ARENA06A={3072,320,24,80,3047,271,104,192,solids06a,15,&scene06a};

static const RoutePoint points06a[]={{112,200,0},{568,200,0},{568,224,1},{816,224,0},{816,144,0},{904,144,0},{1128,144,0},{1128,184,0},{1336,184,1},{1592,184,0},{1592,224,0},{1840,224,0},{1920,224,0},{2088,224,0},{2088,184,1},{2536,184,1},{2944,184,0}};
const RouteDef CAMPAIGN_ROUTE06A={points06a,17,{2912,144,64,48,FALSE}};

static const ArenaRect cameraFocus06b[]={{56,24,102,144,FALSE},{2880,24,128,115,FALSE}};

static const ArenaStream stream06b={1095};
static const ArenaScene scene06b={.tiles=(const u32 *)campaign_route06b_tiles,.map=(const u16 *)campaign_route06b_map,.palette=(const u16 *)campaign_route06b_palette,.tileCount=456,.rows=40,.cols=384,.cameraPlayerY=200,.cameraFocus=cameraFocus06b,.cameraFocusCount=2,.stream=&stream06b,.streamOverlay=TRUE,.cameraSouthStart=192};
static const ArenaRect solids06b[]={{56,80,104,88,TRUE},{2880,80,128,64,TRUE},{320,224,32,16,TRUE},{656,112,80,48,TRUE},{880,240,32,16,TRUE},{1168,248,48,16,FALSE},{1376,128,32,16,TRUE},{1672,112,80,48,TRUE},{1968,248,48,16,FALSE},{2184,240,32,16,TRUE},{2368,128,40,24,FALSE},{832,80,32,32,TRUE},{832,176,32,96,TRUE},{1856,80,32,112,TRUE},{1856,256,32,16,TRUE}};

const ArenaDef CAMPAIGN_ARENA06B={3072,320,24,80,3047,271,104,192,solids06b,15,&scene06b};

static const RoutePoint points06b[]={{112,200,0},{568,200,0},{568,224,1},{792,224,0},{792,160,0},{816,160,0},{816,144,0},{904,144,0},{1128,144,0},{1128,184,1},{1592,184,0},{1592,224,0},{1816,224,0},{1816,240,0},{1840,240,0},{1840,224,0},{1920,224,0},{2088,224,0},{2088,184,1},{2536,184,1},{2944,184,0}};
const RouteDef CAMPAIGN_ROUTE06B={points06b,21,{2912,144,64,48,FALSE}};

static const ArenaRect cameraFocus12[]={{64,24,304,160,FALSE},{688,24,160,128,FALSE},{1200,24,160,128,FALSE},{1712,24,160,128,FALSE},{2224,24,160,128,FALSE},{2720,24,304,176,FALSE}};

static const ArenaScene scene12={.tiles=(const u32 *)campaign_route12_tiles,.map=(const u16 *)campaign_route12_map,.palette=(const u16 *)campaign_route12_palette,.tileCount=618,.rows=40,.cols=384,.cameraPlayerY=200,.cameraFocus=cameraFocus12,.cameraFocusCount=6,.cameraSouthStart=224};
static const ArenaRect solids12[]={{0,0,3072,112,TRUE},{64,24,304,160,TRUE},{688,24,160,128,TRUE},{1200,24,160,128,TRUE},{1712,24,160,128,TRUE},{2224,24,160,128,TRUE},{2720,24,304,176,TRUE},{400,240,32,32,TRUE},{416,128,40,40,TRUE},{720,208,96,64,TRUE},{928,224,40,40,TRUE},{1200,240,32,32,TRUE},{1408,112,96,64,TRUE},{1744,208,96,64,TRUE},{1984,224,40,40,TRUE},{2224,240,32,32,TRUE},{2432,112,96,64,TRUE},{2608,240,32,32,TRUE}};

const ArenaDef CAMPAIGN_ARENA12={3072,320,16,112,3055,287,48,208,solids12,18,&scene12};

static const RoutePoint points12[]={{56,216,0},{632,216,0},{632,176,1},{888,176,0},{1016,176,0},{1016,224,0},{1400,224,0},{1608,224,0},{1608,176,1},{1912,176,0},{2040,176,0},{2040,224,0},{2584,224,1},{2856,224,0}};
const RouteDef CAMPAIGN_ROUTE12={points12,14,{2800,208,160,64,FALSE}};

const ArenaRect CAMPAIGN_ROUTE06_gates[2]={{840,112,16,64,TRUE},{1864,192,16,64,TRUE}};
const RoutePoint CAMPAIGN_ROUTE06B_valves[2]={{792,128,0},{1816,208,0}};
