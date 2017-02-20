import ee, gee
import argparse
gee.init()

#
# CONFIG
#
CRS="EPSG:4326"
SCALE=27.829872698318393
Z_LEVELS=[156000,78000,39000,20000,10000,4900,2400,1200,611,305,152,76,38]
MAX_PIXS=65500
FULL_INTENSITY=255
BANDS=['intensity','blank','lossyear']
PROJECT_ROOT='projects/wri-datalab'
HANSEN_COMPOSITE_IMG='HansenComposite_14-15'
HANSEN_ZLEVEL_FOLDER='HansenZLevel'
THRESHOLDS=[10,15,20,25,30,50,75]
VERSION=None


#
# HELPERS
#
def get_geom(name):
    return ee.Feature(geoms_ft.filter(ee.Filter.eq('name',name)).first())

#
# DATA
#
geoms_ft=ee.FeatureCollection('ft:13BvM9v1Rzr90Ykf1bzPgbYvbb8kGSvwyqyDwO8NI')
world=get_geom('hansen_world').geometry()


#
# Methods:
#
def zintensity(img,z,scale=SCALE,thresh_full=True):
    if thresh_full: img=img.gt(0).multiply(FULL_INTENSITY)
    return img.reproject(
                            scale=scale,
                            crs=CRS
                    ).reduceResolution(
                            reducer=ee.Reducer.mean(),
                            maxPixels=MAX_PIXS
                    ).reproject(
                            scale=Z_LEVELS[z],
                            crs=CRS
                    )


def zlossyear(img,z,scale=SCALE):
    return img.mask(img.gt(0)).reproject(
                            scale=scale,
                            crs=CRS
                    ).reduceResolution(
                            reducer=ee.Reducer.mode(),
                            maxPixels=MAX_PIXS
                    ).reproject(
                            scale=Z_LEVELS[z],
                            crs=CRS
                    )


def zviz(img,z,scale=SCALE):
    return zintensity(img,z,scale).addBands([ee.Image(0),zlossyear(img,z,scale)]).toInt().rename(BANDS)


def zjoin(img_i,img_ly):
    return img_i.addBands([ee.Image(0),img_ly]).toInt().rename(BANDS)


#
# EXPORTERS
#
def export_tiles(image,z):
    name='hansen_composite_py{}'.format(VERSION)
    print('tiles:',z,name)
    task=ee.batch.Export.map.toCloudStorage(
        image=image, 
        description='{}__{}'.format(name,z), 
        bucket='forma-public', 
        path='HANSEN_TEST/byzlevel/{}'.format(name), 
        writePublicTiles=True, 
        maxZoom=z, 
        minZoom=z, 
        region=world.coordinates().getInfo(), 
        skipEmptyTiles=True
    )
    task.start()
    return task


def export_asset(image,z):
    name=zlevel_asset_name(z)
    print('asset:',z,name)
    task=ee.batch.Export.image.toAsset(
        image=image, 
        description=name, 
        assetId='{}/{}'.format(PROJECT_ROOT,name), 
        scale=Z_LEVELS[z], 
        crs=CRS, 
        region=world.coordinates().getInfo(),
        maxPixels=500000000
    )
    task.start()
    return task


#
# RUN
#
def run_in(img,maxz,minz,last_to_asset=False,scale=SCALE):
    for z in range(maxz,minz-1,-1):
        zimg=zviz(img,z,scale)
        task=export_tiles(zimg,z)
        print "z",z,task.status()
    if last_to_asset:
        print 'export asset:',z
        task=export_asset(zimg,z)
        print "z",z,task.status()


def run_out(img_i,img_ly,maxz,minz,scale):
    for z in range(maxz,minz-1,-1):
        zimg_i=zintensity(img_i,z,scale,False)
        zimg_ly=zlossyear(img_ly,z,scale)
        zimg=zjoin(zimg_i,zimg_ly)
        task=export_tiles(zimg,z)
        print "z",z,task.status()


def threshold_composite(threshold):
    return ee.Image(HANSEN_COMPOSITE_IMG).select(['loss_{}'.format(threshold)])


def zlevel_asset_name(z):
    if VERSION: versioning='_v{}'.format(VERSION)
    else: versioning=''
    return 'hansen{}_zlevel_{}'.format(versioning,z)

def zlevel_asset(z):
    return ee.Image('{}/{}'.format(PROJECT_ROOT,zlevel_asset_name(z)))

#
# MAIN
#
def _inside(args):
    hc=threshold_composite(args.threshold)
    hcz=ee.Image(0).where(hc,hc)
    run_in(hcz,args.max,args.min,args.asset)


def _outside(args):
    last_z=args.max+1
    scale=Z_LEVELS[last_z]
    img=zlevel_asset(z)
    img_i=img.select(['intensity'])
    img_ly=img.select(['lossyear'])
    run_out(img_i,img_ly,args.max,args.min,scale)


def main():
    parser=argparse.ArgumentParser(description='HANSEN COMPOSITE')
    parser.add_argument('threshold',help='treecover 2000:\none of {}'.format(THRESHOLDS))
    subparsers=parser.add_subparsers()
    parser_inside=subparsers.add_parser('inside', help='export the zoomed in z-levels')
    parser_inside.add_argument('-max','--max',default=12,help='max level')
    parser_inside.add_argument('-min','--min',default=7,help='min level')
    parser_inside.add_argument('-a','--asset',default=True,help='export min level to asset')
    parser_inside.set_defaults(func=_inside)
    parser_outside=subparsers.add_parser('outside', help='export the zoomed out z-levels')
    parser_outside.add_argument('-max','--max',default=6,help='max level')
    parser_outside.add_argument('-min','--min',default=2,help='min level')
    parser_outside.set_defaults(func=_outside)
    args=parser.parse_args()
    if int(args.threshold) in THRESHOLDS: args.func(args)
    else: print 'INVALID THRESHOLD:',args.threshold,args

    


if __name__ == "__main__":
    main()
