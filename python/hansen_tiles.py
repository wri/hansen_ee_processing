import ee, gee
import argparse
import re
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
GCE_TILE_ROOT='Hansen14_15'
THRESHOLDS=[10,15,20,25,30,50,75]
DEFAULT_GEOM_NAME='hansen_world'
DEFAULT_VERSION=1
TEST_RUN=False
NOISY=True
Z_MAX=12


#
# GEOMETRY
#
geom=None
geom_name=None
geoms_ft=ee.FeatureCollection('ft:13BvM9v1Rzr90Ykf1bzPgbYvbb8kGSvwyqyDwO8NI')
def get_geom(name):
    return ee.Feature(geoms_ft.filter(ee.Filter.eq('name',name)).first()).geometry()


#
# Methods:
#
def zintensity(img,z,scale=SCALE):
    reducer=ee.Reducer.mean()
    return reduce(img,z,scale,reducer)


def zlossyear(img,z,scale=SCALE):
    img=img.updateMask(img.gt(0))
    reducer=ee.Reducer.mode()
    return reduce(img,z,scale,reducer)


def reduce(img,z,scale,reducer):
    if (z==Z_MAX): 
        return img
    else:
        return img.reproject(
                    scale=scale,
                    crs=CRS
            ).reduceResolution(
                    reducer=reducer,
                    maxPixels=MAX_PIXS
            ).reproject(
                    scale=Z_LEVELS[z],
                    crs=CRS
            )


def zjoin(img_i,img_ly):
    return img_i.addBands([ee.Image(0),img_ly]).toInt().rename(BANDS)


#
# EXPORTERS
#
def export_tiles(image,z,v,threshold):
    tiles_path=gce_tiles_path(v,threshold)
    name=tiles_path.replace('/','__')
    print('tiles:',z,tiles_path,name)
    if not TEST_RUN:
        task=ee.batch.Export.map.toCloudStorage(
            fileFormat='png',
            image=image.unmask(0).updateMask(1),
            description='{}__{}'.format(name,z), 
            bucket='wri-public', 
            path=tiles_path, 
            writePublicTiles=True, 
            maxZoom=z, 
            minZoom=z, 
            region=geom.coordinates().getInfo(), 
            skipEmptyTiles=True
        )
        task.start()
        if NOISY: print task.status()
        return task


def export_asset(image,z,v,threshold):
    name=zlevel_asset_name(v,z,threshold)
    print('asset:',z,name)
    if not TEST_RUN:
        task=ee.batch.Export.image.toAsset(
            image=image, 
            description=name, 
            assetId='{}/{}/{}'.format(PROJECT_ROOT,HANSEN_ZLEVEL_FOLDER,name), 
            scale=Z_LEVELS[z], 
            crs=CRS, 
            region=geom.coordinates().getInfo(),
            maxPixels=500000000
        )
        task.start()
        if NOISY: print task.status()
        return task


#
# RUN
#
def run(img_i,img_ly,maxz,minz,v,threshold,scale=SCALE,lowest_to_asset='False'):
    for z in range(minz,maxz+1):
        zimg_i=zintensity(img_i,z,scale)
        zimg_ly=zlossyear(img_ly,z,scale)
        zimg=zjoin(zimg_i,zimg_ly)
        if z==minz:
            if (not lowest_to_asset) or (isinstance(lowest_to_asset,str) and lowest_to_asset.lower()=='false'):
                print 'skiping inside-asset-export'
            else:
                print 'export asset:',z
                task=export_asset(zimg,z,v,threshold)
        task=export_tiles(zimg,z,v,threshold)


def run_zasset(img_i,img_ly,z,v,threshold,scale=SCALE):
    zimg_i=zintensity(img_i,z,scale)
    zimg_ly=zlossyear(img_ly,z,scale)
    zimg=zjoin(zimg_i,zimg_ly)
    print 'export asset:',z
    task=export_tiles(zimg,z,v,threshold)


#
# PATH/IMG/IC HELPERS
#
def gce_tiles_path(v,threshold):
    return '{}/tiles/{}/v{}/tc{}'.format(GCE_TILE_ROOT,geom_name,v,threshold)


def threshold_composite(threshold):
    img_path='{}/{}'.format(PROJECT_ROOT,HANSEN_COMPOSITE_IMG)
    return ee.Image(img_path).select(['loss_{}'.format(threshold)])


def zlevel_asset_name(v,z,threshold):
    gname=re.sub('^hansen','',geom_name)
    gname=re.sub('^_','',gname)
    return re.sub('\.','-','hansen_{}_v{}_z{}_tc{}'.format(gname,v,z,threshold))


def zlevel_asset(v,z,threshold):
    return ee.Image('{}/{}/{}'.format(PROJECT_ROOT,HANSEN_ZLEVEL_FOLDER,zlevel_asset_name(v,z,threshold)))


#
# MAIN
#
def _inside(args):
    img_i, img_ly=_hansen_intensity_lossyear(args.threshold)
    run(img_i,img_ly,int(args.max),int(args.min),args.version,args.threshold,lowest_to_asset=args.asset)


def _outside(args):
    last_z=int(args.max)+1
    scale=Z_LEVELS[last_z]
    img=zlevel_asset(args.version,last_z,args.threshold)
    img_i=img.select(['intensity'])
    img_ly=img.select(['lossyear'])
    run(img_i,img_ly,int(args.max),int(args.min),args.version,args.threshold,scale,False)


def _zasset(args):
    img_i, img_ly=_hansen_intensity_lossyear(args.threshold)
    run_zasset(img_i,img_ly,int(args.z_level),args.version,args.threshold)


def _hansen_intensity_lossyear(threshold):
    hc=threshold_composite(threshold)
    hcz=ee.Image(0).where(hc,hc)
    return hcz.gt(0).multiply(FULL_INTENSITY), hcz


def main():
    global geom_name, geom
    parser=argparse.ArgumentParser(description='HANSEN COMPOSITE')
    parser.add_argument('-g','--geom_name',default=DEFAULT_GEOM_NAME,help='geometry name (https://fusiontables.google.com/DataSource?docid=13BvM9v1Rzr90Ykf1bzPgbYvbb8kGSvwyqyDwO8NI)')
    parser.add_argument('-v','--version',default=DEFAULT_VERSION,help='version')
    parser.add_argument('threshold',help='treecover 2000:\none of {}'.format(THRESHOLDS))
    subparsers=parser.add_subparsers()
    parser_inside=subparsers.add_parser('inside', help='export the zoomed in z-levels')
    parser_inside.add_argument('-max','--max',default=12,help='max level')
    parser_inside.add_argument('-min','--min',default=7,help='min level')
    parser_inside.add_argument('-a','--asset',default='True',help='export min level to asset')
    parser_inside.set_defaults(func=_inside)
    parser_outside=subparsers.add_parser('outside', help='export the zoomed out z-levels')
    parser_outside.add_argument('-max','--max',default=6,help='max level')
    parser_outside.add_argument('-min','--min',default=2,help='min level')
    parser_outside.set_defaults(func=_outside)
    parser_zasset=subparsers.add_parser('zasset', help='export z-level to asset')
    parser_zasset.add_argument('-z','--z_level',default=7,help='max level')
    parser_zasset.set_defaults(func=_zasset)
    args=parser.parse_args()
    if int(args.threshold) in THRESHOLDS: 
        geom_name=args.geom_name
        geom=get_geom(geom_name)
        args.func(args)
    else: 
        print 'INVALID THRESHOLD:',args.threshold,args


if __name__ == "__main__":
    main()
