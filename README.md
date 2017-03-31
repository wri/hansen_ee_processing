#### Hansen Tiles

Hansen Tiles are generated from an EarthEngine asset whose various bands contain the raw Hansen lossyear-data masked by various thresholds of treecover2000.  This same asset is used for the Hansen Analysis API (note tests of the API using this image along with derivative `ImageCollections` can be found [here](https://gist.github.com/brookisme/ff6f557aeb84870e5827c78a5c7ba8f7).

This repo contains:

* [hansen\_ee\_processing/js/composite_asset.js](#hasset): javascript code to produce the most recent version of the Hansen Asset described above
* [hansen\_ee\_processing/python/hansen_tiles.py](#htiles): python script that generates the hansen tiles (in 2 steps).

---
<a name='hasset'></a>
#### Hansen Composite 14-15
To re-generate this asset simply run the code. The current [Hansen Asset](https://code.earthengine.google.com/?asset=projects/wri-datalab/HansenComposite_14-15) is unique because it merges data from Hansen 2014 and Hansen 2015. Therefore process probably won't need to be repeated.  That said, the second half of the code, starting around [here](https://github.com/wri/hansen_ee_processing/blob/master/js/composite_asset.js#L52) could easily be modified to create future assets.


---
<a name='htiles'></a>
#### Hansen Tiles

Do to the earthengine limits discussed [here](https://groups.google.com/forum/#!topic/google-earth-engine-developers/wU4NNoWTD70) we had to process the tiles in 2 steps:

1. Export Tiles for zoom-levels 12-7, And export an earthengine asset for zoom-level 7
2. Export Tiles for zoom-levels 7-2

The code can be run via the command line:

```bash
# step 1
$ python hansen_tiles.py inside

# step 2 (after the earth engine asset for zoom-level 7 has completed processing)
$ python hansen_tiles.py outside
```

There are various options like runing over test geometries, changing the versioning, changing the zoom-level used as a break between step 1 and 2, and more.

```bash
python|master $ python hansen_tiles.py -h
usage: hansen_tiles.py [-h] [-g GEOM_NAME] [-v VERSION]
                       threshold {inside,outside,zasset} ...

HANSEN COMPOSITE

positional arguments:
  threshold             treecover 2000: one of [10, 15, 20, 25, 30, 50, 75]
  {inside,outside,zasset}
    inside              export the zoomed in z-levels
    outside             export the zoomed out z-levels
    zasset              export z-level to asset

optional arguments:
  -h, --help            show this help message and exit
  -g GEOM_NAME, --geom_name GEOM_NAME
                        geometry name (https://fusiontables.google.com/DataSou
                        rce?docid=13BvM9v1Rzr90Ykf1bzPgbYvbb8kGSvwyqyDwO8NI)
  -v VERSION, --version VERSION
                        version
 ```


