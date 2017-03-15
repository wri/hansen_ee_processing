var CRS="EPSG:4326"
var SCALE=27.829872698318393
var Z_LEVELS=[156000,78000,39000,20000,10000,4900,2400,1200,611,305,152,76,38]
var MAX_PIXS=65500
var FULL_INTENSITY=255
var BANDS=['intensity','blank','lossyear']
var PROJECT_ROOT='projects/wri-datalab'
var HANSEN_COMPOSITE_IMG='HansenComposite_14-15'
var HANSEN_ZLEVEL_FOLDER='HansenZLevel'
var GCE_TILE_ROOT='Hansen14_15'
var THRESHOLDS=[10,15,20,25,30,50,75]
var DEFAULT_GEOM_NAME='hansen_world'
var DEFAULT_VERSION=1
var TEST_RUN=false
var NOISY=true
var Z_MAX=12

var tc=10
var hc=h1415.select(['loss_'+tc])
var hcz=ee.Image(0).where(hc,hc)
var hci=hcz.gt(0).multiply(FULL_INTENSITY)
//
// GEOMETRY
//
var geom=null
var geom_name=null
var geoms_ft=ee.FeatureCollection('ft:13BvM9v1Rzr90Ykf1bzPgbYvbb8kGSvwyqyDwO8NI')
var get_geom=function(name){
    return ee.Feature(geoms_ft.filter(ee.Filter.eq('name',name)).first()).geometry()
}

//
// Methods:
//
var zintensity=function(img,z,scale){
    if (!scale) scale=SCALE
    var reducer=ee.Reducer.mean()
    return reduce(img,z,scale,reducer)
}

var zlossyear=function(img,z,scale){
    if (!scale) scale=SCALE
    img=img.updateMask(img.gt(0))
    var reducer=ee.Reducer.mode()
    return reduce(img,z,scale,reducer)
}

var reduce=function(img,z,scale,reducer){
    if (z==Z_MAX){ 
        return img
    } else {
        return img.reproject({
                    'scale':scale,
                    'crs':CRS
            }).reduceResolution({
                    'reducer':reducer,
                    'maxPixels':MAX_PIXS
            }).reproject({
                    'scale':Z_LEVELS[z],
                    'crs':CRS
            })
    }
}


var zjoin=function(img_i,img_ly){
    return img_i.addBands([ee.Image(0),img_ly]).toInt().rename(BANDS)
}

//
// MAP
//

var addz=function(z){
  var inten=zintensity(hci,z)
  var loss=zlossyear(hc,z)
  Map.addLayer(zjoin(inten,loss),null,'z_'+z)
}
Map.addLayer(hc,null,'ht')
addz(12)
addz(10)
addz(8)
addz(6)
addz(5)
Map.centerObject(pt,12)
