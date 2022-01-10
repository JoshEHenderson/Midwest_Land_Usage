# Imports                          # USES:
import rasterio as rio             # handling tif files
import rasterio.plot as rioplt     # viewing the images from tif files
from shapely.geometry import Point # making points for each of the pixels
from shapely import ops as shpops  # transforming data between projections (works with pyproj)
import pyproj                      # creating a projection to be used in the shpops transformation
import matplotlib.pyplot as plt    # plotting data
import numpy as np                 # number handling and arrays
import pandas as pd                # creating dataFrames to hold information
import geopandas as gpd            # handling GeoDataframes
from tqdm import trange            # progress bar
from tqdm import tqdm              # progress bar
import logging                     # Redirecting warnings to keep output clean

logging.captureWarnings(capture=True) # Redirect warnings to the logs

# =============================================================================
# LOAD THE IMAGE
# =============================================================================

# Read in tif files (Only years 2004-2020 were present in the file)
rio_all_img = [rio.open('land_use_data/CDL_2004_clip_20211207232419_873250894.tif'), rio.open('land_use_data/CDL_2008_clip_20211207232419_873250894.tif'), rio.open('land_use_data/CDL_2012_clip_20211207232419_873250894.tif'), rio.open('land_use_data/CDL_2016_clip_20211207232419_873250894.tif'), rio.open('land_use_data/CDL_2020_clip_20211207232419_873250894.tif')]

# PRINT TRANSFORMATION MATRICES
year = [2004, 2008, 2012, 2016, 2020]   # Years present
nImg = len(rio_all_img)                 # Number of images

#print("Transformation matrices for all",nImg,"images by year")
#for x, img in enumerate(rio_all_img):   # for each tif file
#    print(year[x])                      # print the year
#    print(img.transform)                # print the transformation matrix
    
# All the matrices are the same, so I will just print out one of them
print("Transformation Matrix")
print(rio_all_img[0].transform) # print the transformation matrix from 2004 since they are all the same

# View the images
#for img in rio_all_img:
#    rioplt.show( img )

# GET THE UNIQUE VALUES BETWEEN ALL IMAGES
print("\nFinding Unique Values")
uniqueValues = set()                        # Set for storing unique values
for n, img in enumerate(rio_all_img):       # For each "image"
    currImg = img.read()[0]                 #   Read the image
    print("Year:",year[n])                  # Print the year for tracking purposes
    for row in tqdm(currImg):               #   create a progress bar
        for val in row:                     #   Iterate over every value
            uniqueValues.add(val)           #       Add each value to the set
uniqueValues = sorted(list(uniqueValues))   # Convert the unique values into a sorted list

# GET THE VALUE COUNTS FOR EACH IMAGE
print("\nFinding Value Counts")
valueCounts = []                                # List to store value counts (will be a list of lists, length 5, one for each image)
for n, img in enumerate(rio_all_img):           # For each "image"
    valCount = [0 for i in range(len(uniqueValues))]    # Initialize its value counts to 0
    currImg = img.read()[0]                             # Read the image
    print("Year:",year[n])                              # Print the year for tracking purposes
    for row in tqdm(currImg):                           # create a progress bar
        for val in row:                                 # Iterate over every value
            valCount[uniqueValues.index(val)] += 1      # Increment the value count, indexed parallelly to uniqueValues
    valueCounts.append(valCount)                        # Add the list of value counts for the current image to the list of lists
    #print(np.sum(valCount), " = ", currImg.shape[0]*currImg.shape[1])  # make sure the number of values found matches the number of pixels

maxVal = max([max(valueCounts[i]) for i in range(len(valueCounts))])    # get the max value so the limit can be set on the bar graph

# PRINT A BAR CHART FOR EACH YEAR (aka each image)
for i, yr in enumerate(year):               # For each year
    plt.bar(uniqueValues, valueCounts[i])   #   make a bar graph of the value counts for each value
    plt.title(yr)                           #   set the title to the year
    plt.ylim(top=maxVal)                    #   limit the y axis so all graphs have the same limit
    plt.show()                              #   show the bar graph

# Hypothesis about top 5 usage: Corn, Soybeans, Alfalfa, Cities, Grass

usage_df = pd.read_csv('region_stats.csv')  # land usage data
#print(usage_df)                            # Data Exploration
#print(usage_df.columns)                    # Data Exploration
print(usage_df.sort_values(by=[' Count'], ascending=False).head(5)[' Category']) # print the top 5 categories by count

# Actual Top 5 categories: Corn, Soybeans, Grass/Pasture, Developed/Open Space, Deciduous Forest

top5 = [' Corn', ' Soybeans', ' Grass/Pasture', ' Developed/Open Space', ' Deciduous Forest']
top5Index = [usage_df[usage_df[' Category'] == cat]['Value'].iloc[0] for cat in top5]
#print(top5Index)

'''
# Notes: There are 38 values in the provided csv. This leads me to believe it is only from 2020
#        2020 has 39 unique values, 38 of which are non-zero. All other years have different numbers of unique values
#        As the number of zero values in each year is the exact same, I assume those are the null values around the outside of the image
#        However, I will analyze the top 5 from my findings in 2020, excluding the zero-values
#            and will use those categories as the top 5 categories for future analysis.
#        I will also explore the top 5 category numbers in each year though for curiosity's sake
'''

# CREATE A DATAFRAME CONTAINING VALUES, CATEGORY NAMES, AND VALUE COUNTS FOR EACH YEAR
value_df = pd.DataFrame()       # DataFrame for storing the values, category name, and their count for each year
value_df['ID'] = uniqueValues   # Get the IDs from the list of unique values across all images
catList = []                    # For developing a list of categories for each ID if they exist
for i in value_df['ID']:                            # For each value, storing the value as i
    curr = usage_df[usage_df['Value'] == i]         #   Try to retreive the row in usage_df where value is equal to i
    if len(curr) > 0:                               #   Length of 1 means it is in the usage_df. Length of 0 means it isn't
        catList.append(curr[' Category'].iloc[0])   #       If it is in the usage_df, get the name of that category
    elif i == 0:                                    #   Else, if it is 0
        catList.append("Null")                      #       hypothesize that it is a null value
    else:                                           #   Else, I don't know what it is
        catList.append("n/a")                       #       So, append "n/a"
value_df['Category'] = catList                      # Then, add the category list as a column in the dataframe
                                                    #
for x, yr in enumerate(year):                       # For each year,
    value_df[yr] = valueCounts[x]                   # Add the list of value counts for that year to the DataFrame
#print(value_df)        # Exploration
#print(value_df.info()) # Exploration

# NOTE: I kept zero values in the dataframe instead of just gettting rid of them intentionally to keep track of how many there were

# Find what the top 6 values in each year were (top 5 plus zero)
#for yr in year         # For each year
#    print("\t\t",yr)   # Print the year, then the top 6 values for that year
#    print(value_df.sort_values(by=[yr], ascending=False).head(6)['Category'])
#    print()

'''
# NOTES:
# The Top 5 Categories for years 2008, 2012, 2016, and 2020 were he same as in the usage_df
#     with the addition of the category with value 0
# For 2004, the top categories were corn, soybeans, grass/pasture, the value 0, the value 35, and the value 30
#     however, the values 35 and 30 were not in the provided csv, so their categories are unknown.
'''

# Size of each pixel: 30m x 30m=

# =============================================================================
# LOAD IOWA COUNTY BOUNDARIES
# =============================================================================

counties_gdf = gpd.read_file('US_counties/cb_2018_us_county_5m.shp')    # Read in GeoDataFrame
#print(counties_gdf.info()) # Exploring
counties_gdf = counties_gdf[counties_gdf.STATEFP == '19']               # Retrieve only entries from IOWA
countyNm = ['Black Hawk', 'Butler', 'Franklin', 'Carroll', 'Webster']   # Counties to be retrieved
new_gdf = gpd.GeoDataFrame()                                            # Create a new GeoDataFrame for values from the 5 counties
for nm in countyNm:                                                     # For each county
    new_gdf = new_gdf.append(counties_gdf[counties_gdf.NAME == nm])     # Append its row from the counties gdf to the new gdf

#print(new_gdf)                         # look at the new data
#print(new_gdf.NAME.unique())           # make sure the correct counties were retrieved
#print(len(new_gdf))                    # make sure no two counties have the same name (check for length == 5)
#print(type(new_gdf.geometry.iloc[0]))  # check if the polygons in the gdf are stored as shapely polygons

# GET THE POLYGONS FOR EACH COUNTY AND PROJECT TO UTM ZONE 15 (same as the tif files)
bounds = [new_gdf.geometry.iloc[i] for i in range(5)]   # Get a list of the polygons for each county
boundary_prj = []                                       # For holding projected polygons
wgs84 = pyproj.CRS('EPSG:4326')                         # Old Projection 
new_crs = pyproj.CRS( str(rio_all_img[0].crs) )         # New Projection (the coordinate reference system of the tif files)
# create a transformer that will change polygons from the old to the new projection, keeping the axis order as always being x, y
proj = pyproj.Transformer.from_crs( wgs84, new_crs, always_xy=True ).transform 
for poly in bounds:                                      # For each polygon
    boundary_prj.append(shpops.transform(proj, poly))    #   Transform into new projection

#print(boundary_prj[0]) # make sure projections worked

countyA = []                    # Store the area of each county in a list for future use
for poly in boundary_prj:       # For each polygon,
    countyA.append(poly.area)   #   Store the area of that polygon

print("\nCounty: area")           # Print out the size of each county to the screen
for i in range(5):              # For each county
    print(f"{countyNm[i]}: {countyA[i]}") # print the area

# =============================================================================
# COMPUTE THE LAND USE OF EACH COUNTY FOR EACH YEAR
# =============================================================================

# ===== NOTES =====
# For each state, create a graph
# On each graph, include 5 lines
# These lines represent each of the top 5 land use categories as defined earlier
# These lines will plot the usage of land in the top 5 categories as a percentage of county size by year
# 
# Steps to complete:
#   for each year, loop through every pixel
#       at each pixel, check if it is in one of the counties
#           if so, check if it is one of the categories we need
#               if so, increment the appropriate place in the usage array
#   for each value in the usage array,
#       multiply by 900 (pixels are 30m x 30m = 900m^2)
#       divide by county area
# === END NOTES ===

xSt = 305955    # start location of x
ySt = 4764915   # start location of y
step = 30       # Each pixel is 30m

#print(rio_all_img[0].read().shape) # Exploration: shape contains (1, y(height), x(width))

print("\nComputing Land Usage")
landUsage = np.zeros((5, 5, 5)) # 5 counties, 5 categories being tracked, 5 years, initialized to 0
img = [ rio_all_img[i].read()[0] for i in range(5) ]            #   store all read images
for y in trange(img[0].shape[0]):                               #   make a progress bar that tracks rows
    for x in range(img[0].shape[1]):                            #   iterate over the pixels in each row
        currPt = Point(xSt+(x*step), ySt-(y*step))              #       create a point from the current pixel using transformation matrix
        for county, bound in enumerate(boundary_prj):           #       check each county
            if(bound.contains(currPt)):                         #           if the current point is in a county being tracked
                for yr, curr in enumerate(img):                 #           for each year
                    val = curr[y][x]                            #               get the point's value (y comes before x in the tif files)
                    for category, cat in enumerate(top5Index):  #               check each of the 5 categories being tracked
                        if val == cat:                          #                   if the value is one of the categories being tracked
                            landUsage[county][category][yr] += 1#                       increment the usage for the current county, category, and year
landUsage *= 900                                                # Multiply all values by 900 (area of a pixel)
for i, curr in enumerate(landUsage):                            # For each county
    curr /= countyA[i]                                          #   Divide all values by the area of that county

# print(landUsage)                                              # Explore the resulting array

# Exploration for determining why there are two zero-values in each county for the year 2004
#uniques = set()
#currImg = rio_all_img[0].read()[0]
#for row in currImg:
#    for val in row:
#        uniques.add(val)
#print(sorted(list(uniques)))
#print(top5Index)

# NOTE: Values 121 and 141 aren't present in the 2004 image. Therefore, they have a value of 0

# GRAPH THE PERCENTAGE OF LAND USE FOR EACH COUNTY OVER THE YEARS
c = ['b', 'darkred', 'y', 'c', 'k']                                 # Make the colors easier to distinguish (I'm colorblind)
for n, county in enumerate(countyNm):                               # For each county
    for i, cat in enumerate(landUsage[n]):                          #   For the land usage percentages of each category
        plt.plot(year, cat, label = top5[i].strip(), color = c[i])  #       Graph the percentages by year
    plt.title(county)                                               # Title the graph with the county
    plt.xlabel("Year")                                              # X-Axis represents year
    plt.ylabel("Amount of Total Land Used")                         # Y-Axis represents amount of land used
    plt.legend(bbox_to_anchor=(1, 1))                               # Add an axis outside the graph
    plt.ylim(bottom=-.05, top=0.6)                                  # Make a uniform y axis for all graphs (from observations)
    plt.show()                                                      # Plot that county