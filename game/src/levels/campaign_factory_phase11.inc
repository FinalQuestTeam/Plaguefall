// Generated phase11: shared phase10 tiles/map with blue brick palette.
static const u16 phase11Palette[16]={0,546,1602,1092,2148,1672,2184,2764,1568,2114,2658,3200,1090,1638,2182,1124};
static const ArenaScene phase11Scene={.tiles=phase10Tiles,.map=phase10Map,.palette=phase11Palette,.tileCount=320,.rows=68,.cols=96,.cameraPlayerY=184,.stream=&phase10Stream,.streamOverlay=TRUE,.cameraSouthStart=352};
const ArenaDef CF_FACTORY_REHEAT={768,544,24,128,743,479,56,160,phase10Solids,6,&phase11Scene};
