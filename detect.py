import rasterio as rio
import numpy as np
import os
from scipy import ndimage
from datetime import datetime
from datetime import timezone
from rasterio.enums import ColorInterp
from sun_angle import get_angle
import statistics
import math

meta1= {"name1":
"source/T40VFJ_20210606T071619_B02_60m.jp2",
"name2": "source/T40VFJ_20210606T071619_TCI_60m.jp2"
,"date":datetime(2021,6,6,13,16,19),"timesift":5,"coords":(59.33,57.13),
"limit1": 7000,
"limit2": 100,
"sun_k": 100,
"shadow_coord":(1230,545),
"az_shift":6}

meta2= {"name1":
"source/T41VMD_20220524T070631_B02_60m.jp2",
"name2": "source/T41VMD_20220524T070631_TCI_60m.jp2"
,"date":datetime(2022,5,24,13,6,31),"timesift":5,"coords":(62.2595,57.235),
"limit1": 6000,
"limit2": 1350,
"sun_k": 100,
"shadow_coord":(1230,545),
"az_shift":-3}
max = 0
def draw_shadow(vector,x_c,y_c):
    with rio.open("test2.jp2", 'r+') as src:
        with rio.open("test.jp2", 'r') as clouds:
            with rio.open("source/cloud.png", 'r') as new_cloud:
                bands = src.read()
                nc = new_cloud.read(1)
                cs = src.read(1)
                for x in range(new_cloud.width)[::-1]:
                    for y in range(new_cloud.height)[::-1]:
                        if nc[x,y]:
                            bands[0][x_c+x,y_c+y] = nc[x,y]
                            bands[1][x_c+x,y_c+y] = nc[x,y]
                            bands[2][x_c+x,y_c+y] = nc[x,y]
                            s_x = x_c+x + int(vector[0])    
                            s_y = y_c+y + int(vector[1])
                            if cs[s_x,s_y]<60:
                                s_x = x_c+x + int(vector[0])    
                                s_y = y_c+y + int(vector[1])
                                bands[0][s_x,s_y] = 0
                                bands[1][s_x,s_y] = 0
                                bands[2][s_x,s_y] = 0
                src.write(bands)      

def calc_ele(r,angl):
    return r * math.sin(angl) / math.cos(angl)
def get_r(point1,point2):
    if (not point1[0]*point1[1]*point2[0]*point2[1]):
        return 0
    return math.sqrt((point1[0]-point2[0])**2+(point1[1]-point2[1])**2)*60
def make_points(coords,schema):
    with rio.open("test2.jp2", 'r') as src:
        bands = src.read()
        for c in coords:
            x = int(c[0])
            y = int(c[1])
            if(src.width < x+2 or src.height < y+2):
                 continue
            bands[0][x,y] = schema[0]
            bands[1][x,y] = schema[1]
            bands[2][x,y] = schema[2]

            bands[0][x+1,y] = schema[0]
            bands[1][x+1,y] = schema[1]
            bands[2][x+1,y] = schema[2]

            bands[0][x-1,y] = schema[0]
            bands[1][x-1,y] = schema[1]
            bands[2][x-1,y] = schema[2]

            bands[0][x,y+1] = schema[0]
            bands[1][x,y+1] = schema[1]
            bands[2][x,y+1] = schema[2]

            bands[0][x,y-1] = schema[0]
            bands[1][x,y-1] = schema[1]
            bands[2][x,y-1] = schema[2]
        profile = src.profile
        print(profile)
        with rio.open("test2.jp2","w",**profile) as tt:
            tt.colorinterp = [ColorInterp.red, ColorInterp.green, ColorInterp.blue]
            tt.write(bands)   



        print({i: dtype for i, dtype in zip(src.indexes, src.dtypes)})

def gen(value):
    global max
    if value[0] > max:
        max = value[0]
    if value > meta1["limit1"]:
        return 255
    else:
        return 0

def gen2(value):
    if value < meta1["limit2"]:
        return 255
    else:
        return 0        




def get_с(az, ze):
    az_p= az * np.pi / 180.
    ze_p = ze * np.pi / 180.
    x = np.sin(ze_p) * np.cos(az_p)
    y = np.sin(ze_p) * np.sin(az_p)
    
    return (x, y)




    

def get_cloud_shadows(path, azim, altit):
    with rio.open(path, 'r') as src:
        band = src.read(1)
        band = ndimage.generic_filter(band,gen,1)
        band = ndimage.gaussian_filter(band, sigma=4)
        profile = src.profile
        profile.update(dtype=rio.uint8, count=1, compress='lzw')
        with rio.open("test.jp2","w",**profile) as tt:
            tt.write(band,1)
        with rio.open("test3.jp2","w",**profile) as tt:
            bandd = src.read(1)
            bandd = ndimage.generic_filter(bandd,gen2,1)
            bandd = ndimage.gaussian_filter(bandd, sigma=4)
            tt.write(bandd,1)   
    
    azimuth = azim
    azimuth += 90
    
    
    lbl, n_features = ndimage.label(band)
    centroids = np.array(ndimage.center_of_mass(band, lbl, np.arange(1, n_features - 1))[::])
    make_points(centroids,[0,0,255])

    x_sun, y_sun = get_с(azim, altit)
    
    height, width = band.shape

    s_centroids = [[int(c[0] + x_sun*meta1["sun_k"]),int(c[1] + y_sun*meta1["sun_k"])] for c in centroids]
    
    make_points(s_centroids,[255,0,255])

    shadow_points = [(0,0)] * len(s_centroids)
    cloud_points = [(0,0)] * len(s_centroids)
    for i in range(len(s_centroids)):
        x = [int(centroids[i][0]),int(s_centroids[i][0])]
        y = [int(centroids[i][1]),int(s_centroids[i][1])]
        coefficients = np.polyfit(x, y, 1)
        polynomial = np.poly1d(coefficients)
        x_axis = np.linspace(x[0],x[1],x[0]-x[1])
        y_axis = polynomial(x_axis)    
        for a in range(len(x_axis)):        
                if x_axis[a] > width-1 or x_axis[a] < 0:
                    continue
                if y_axis[a] > height-1 or y_axis[a] < 0:
                    continue
                if bandd[int(x_axis[a]),int(y_axis[a])] > 30:
                    shadow_points[i] = (int(x_axis[a]),int(y_axis[a]))
                if band[int(x_axis[a]),int(y_axis[a])] > 30:
                    cloud_points[i] = (int(x_axis[a]),int(y_axis[a]))
    make_points(cloud_points,[255,128,0])
    make_points(shadow_points,[255,0,0])
    altit = altit*math.pi/180
    azim = azim * math.pi / 180
    heights_p = [(centroids[i],calc_ele(get_r(cloud_points[i],shadow_points[i]),altit)) for i in range(len(cloud_points))]
    heights = [calc_ele(get_r(cloud_points[i],shadow_points[i]),altit) for i in range(len(cloud_points))]
    heights = [h for h in heights if h!=0.0]
    print(heights)
    median_r = statistics.median(heights)
    print(np.array(heights_p))
    print(median_r)
    vector = (np.sin(altit) * np.cos(azim) * median_r/60, np.sin(altit) * np.sin(azim)* median_r/60)
    draw_shadow(vector,*meta1["shadow_coord"])


az,al = get_angle(*meta1["coords"],meta1["date"],meta1["timesift"])
os.popen("cp {} test2.jp2".format(meta1["name2"]))
get_cloud_shadows(meta1["name1"],az+meta1["az_shift"],al)
    
