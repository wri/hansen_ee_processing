var geoms=ee.FeatureCollection('ft:13BvM9v1Rzr90Ykf1bzPgbYvbb8kGSvwyqyDwO8NI')
var h14=ee.Image('UMD/hansen/global_forest_change_2015')
//
// SETUP
//
var CRS="EPSG:4326"
var SCALE=27.829872698318393
var COMPOSITE_IMG_NAME='HansenComposite_14-15-new'

//
// FUSION TABLE GEOMS
//
var get_flat_geom=function(name){
  var coords=ee.Feature(geoms.filter(ee.Filter.eq('name',name)).first()).geometry().coordinates()
  return ee.Geometry.Polygon(coords,null,false)
}
var world_geom=get_flat_geom('hansen_world')
var geom_14=get_flat_geom('hansen_14')
var geom_15=get_flat_geom('hansen_15')
// Map.addLayer(world_geom)
Map.addLayer(geom_14,null,'geom_14')
Map.addLayer(geom_15,null,'geom_15')

//
// Hansen 2014 Data
//
var tc=h14.select(['treecover2000'])
var ly14=h14.select(['lossyear']).clip(geom_14).rename(['lossyear'])
ly14=ly14.mask(ly14)


//
// Hansen 2015 Data
//
var sea_aus=ee.Image('users/amkrylov/Loss2015/SEAAUS_loss_2000-2015')
var sa_a=ee.Image('users/amkrylov/Loss2015/Loss2015')
var ly15=ee.ImageCollection([sea_aus,sa_a]).reduce(ee.Reducer.max(),4).rename(['lossyear']).clip(geom_15)

//
// CompositeData 14-15
//
var ly=ee.ImageCollection([ly15,ly14]).reduce(ee.Reducer.firstNonNull()).rename(['lossyear'])

// //
// // Map
// //
// Map.addLayer(ly,{palette:['ff0000'],min:0, max:15},'ly')
Map.addLayer(ly14.mask(ly14),{palette:['00ff00'],min:0, max:15},'ly14')
Map.addLayer(ly15.mask(ly15),{palette:['0000ff'],min:0, max:15},'ly15')

//
// Thresholding
//
var tree=function(thresh){
  return tc.updateMask(tc.gte(thresh)).rename(['tree_'+thresh])
}
var loss=function(thresh){
  return ly.updateMask(tc.gte(thresh)).rename(['loss_'+thresh])
}
var thresholds=[10,15,20,25,30,50,75]
var threshold_images=[]
for (var i=0; i<thresholds.length; i++) {
  threshold_images.push(tree(thresholds[i]))
  threshold_images.push(loss(thresholds[i]))
}
var threshold_image=ee.Image(threshold_images)
// print(threshold_image)

//
// GAIN (from old asset)
//
var hgain=ee.Image('HANSEN/gfw2015_loss_tree_gain_threshold').select(['gain'])
// print(hgain)

//
// FINAL IMAGE
//
var hansen_composite=threshold_image.addBands([hgain])
Map.addLayer(hansen_composite,null,'HansenComposite')
print(hansen_composite)


//
// Exporter
//
var ppolicy={
  'tree_10':'mean',
  'loss_10':'mode',
  'tree_15':'mean',
  'loss_15':'mode',
  'tree_20':'mean',
  'loss_20':'mode',
  'tree_25':'mean',
  'loss_25':'mode',
  'tree_30':'mean',
  'loss_30':'mode',
  'tree_50':'mean',
  'loss_50':'mode',
  'tree_75':'mean',
  'loss_75':'mode',
  'gain':'mean'
}

var export_asset=function(img,name){
  Export.image.toAsset({
    'image':img, 
    'description':name, 
    'assetId':'projects/wri-datalab/'+name, 
    'scale':SCALE, 
    'crs':CRS, 
    'region':world_geom.coordinates(),
    'pyramidingPolicy':ppolicy,
    'maxPixels':800000000000
  })
}

export_asset(hansen_composite,COMPOSITE_IMG_NAME)

