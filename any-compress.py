#!/usr/bin/env python
# coding: utf-8

# In[ ]:


"""Compression script which leads to a ~80% reduction in image size, without compromising EXIF data or reducing quality 
too much."""

# Imports the necessary libraries for the script to run.
# If the script fails to run and it says that it's missing one of these libraries, then use the pip install command in cmd.exe
from datetime import datetime
import logging
from pathlib import Path
import PIL
from PIL import Image
import os
try:
    from os import scandir
except ImportError:
    from scandir import scandir
import glob
import win32con, win32api
import time

import osgeo.ogr as ogr
import osgeo.osr as osr
from PIL.ExifTags import GPSTAGS
from PIL.ExifTags import TAGS
import numpy as np
import csv

# datetime object containing current date and time
date_time = datetime.now()
# dd/mm/YY H:M:S
dt_format = date_time.strftime("%d-%m-%Y %Hh %Mm %Ss")


# Sets the format for the Log File.
logging.basicConfig(filename='E:\\webserver\\Python Script Logs\\any-compress\\'+dt_format+'.csv', format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
logging.warning(",Script Started. *******************************************************************************************************************************")

"""When setting PATHS below, make sure that you follow the format which is used. 
If your path in windows is: C:\webserver\data\prod\rep1\shp, then you must type it as: C:\\webserver\data\\prod\\rep1\\shp
Make sure to also use the correct number of backslashes, if there is a backslash at the end of the path in the script, make
sure that you have one in yours."""
print('Before starting this script make sure that you have \n 1. Created an Alias in the Apache Vhosts config file for your parent directory which hosts the images and for the Panoviewer \n 2. Created the relevant directory in the E:\webserver\panoviewer\ folder for your html files to be stored in.\n')

print('If you are intending to run this script so that it overwrites an existing photos.shp file, then make sure you do not have a QGIS project open which contains this file and make sure \n that you close any instances of qgis_mapserv.fcgi.exe running on AP086 (this can be done using task manager) \n otherwise you may encounter an error.\n')

# Sets the parent directory to search recursively from (end without any backslashes).
parent_dir = input('Enter the parent directory to search for images. ¦ Note: Case Sensitive, end your directory without a backslash. e.g. '+"\\\\"+'fs008\WebmapsFTP\YW  ...')
parent_dir = str(parent_dir)
print(parent_dir)
print('')
# Set this to match an alias that you want to point to (should match the alias you use in Apache Vhosts Config).
# e.g. if your alias is /edf/ in Apache, then it must be 'edf' in this Script.
alias = input('Enter the website alias e.g. yw, ftp, edf, webgis, etc. Do not include any backslash or forward slash. ¦ Note: Case Sensitive  ...')
print(alias)
print('')
# Sets the path where the CSV and SHP file will be created (end with two backslashes).
csv_shp_path = input('Enter output path for the SHP file and CSV ¦ Note: Case Sensitive, end your directory without a backslash. e.g. E:\webserver\data\prod\\rep1\shp  ...')
csv_shp_path = csv_shp_path + "\\"
shp_file_outpath = csv_shp_path + 'photos.shp' # Sets the name of the output SHP file.
csv_path = csv_shp_path + 'import-geotag.csv' # Sets the name of the output CSV file.
missed_images_csv_path = 'E:\\webserver\\Python Script Logs\\any-compress\\' + dt_format + ' missed-images.csv'
print(csv_shp_path)
print('')
# This sets the directory where you want to create the html files for 360 photos (end with two backslashes).
# Only change this if you have moved your host location for the panoviewer.
html_output_path = input('\n*********If you know that you do not have any 360 photos, just leave this blank********* \n Enter the output directory for the html files ¦ Note: Case Sensitive, end your directory without a backslash. e.g. E:\webserver\panoviewer\YW  ...')
html_output_path = html_output_path + "\\"
print(html_output_path)
print('')
# Sets the link to the panoviewer website (This website is set by the 'pano' alias in Apache Vhosts).
# Only change this if you have moved your host location for the panoviewer.
website = '//webmaps.freedom-group.co.uk/'
pano360 = website + input('\n*********If you know that you do not have any 360 photos, just leave this blank********* \n Enter the website alias for the panoviewer e.g. panoYW, panoEDF. do not include any blackslash or forwardslash ¦ Note: Case Sensitive  ...')
print(pano360)
print('')

no_geotags = ""
no_xmp = ""

# In[ ]:

# Starts a timer for the script.
tstart = time.time()

# Search every directory and file within the parent_dir.
for dirName, subdirList, fileList in os.walk(parent_dir): 
# Assign dirName to a variable.
    folder_list = dirName 
# Loops through each directory, if there are directories called 'Compressed', they are ignored.
    if 'Compressed' in folder_list: 
        pass 
    else:
# For every other directory, a new 'Compressed' folder is created.
        try: 
            folder_name = folder_list +'\\Compressed'
            os.mkdir(folder_name)
# This then hides the folder.
            win32api.SetFileAttributes(folder_name, win32con.FILE_ATTRIBUTE_HIDDEN) 
# This ignores a python error which comes up when it tries to create a folder which already exists.
        except OSError as error: 
            pass 
logging.warning(",Hidden Compressed Folders Created.")


# In[ ]:


# This function creates a html file in the exact format as shown below.
def htmloutput(path, html_name):
    text = '''<!DOCTYPE html>
    <html>
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="initial-scale=1, maximum-scale=1, user-scalable=no, width=device-width, shrink-to-fit=no">
        <title>Freedom-Group 360 Viewer</title>
        <style>
          html, body {
            margin: 0;
            width: 100%;
            height: 100%;
            overflow: hidden;
            background-color: #000;
          }
          a:link, a:visited{
            color: #bdc3c7;
          }
          #progress {
            width: 0;
            height: 10px;
            position: fixed;
            top: 0;
            background: #fff;
            -webkit-transition: opacity 0.5s ease;
            transition: opacity 0.5s ease;
          }
          #progress.finish {
            opacity: 0;
          }
          .credit{
            position: absolute;
            text-align: center;
            width: 100%;
            padding: 20px 0;
            color: #fff;
          }
        </style>
      </head>
      <body>
        <div id="progress"></div>
        <script src="js/three.min.js"></script>
        <script src="js/panolens.min.js"></script>
        <script>
            var progressElement;
            progressElement = document.getElementById( 'progress' );
            function onEnter ( event ) {
                progressElement.style.width = 0;
                progressElement.classList.remove( 'finish' );
            }
            function onProgress ( event ) {
                progress = event.progress.loaded / event.progress.total * 100;
                progressElement.style.width = progress + '%';
                if ( progress === 100 ) {
                progressElement.classList.add( 'finish' );
                }
            }
            function onProgress ( event ) {
                progress = event.progress.loaded / event.progress.total * 100;
                progressElement.style.width = progress + '%';
                if ( progress === 100 ) {
                progressElement.classList.add( 'finish' );
                }
            }
            const panorama = new PANOLENS.ImagePanorama( '''+ "'" + path + "'" +''' );
            panorama.addEventListener( 'progress', onProgress );
            panorama.addEventListener( 'enter', onEnter );
            const viewer = new PANOLENS.Viewer( { output: 'console' } );
            viewer.add( panorama );
        </script>
      </body>
    </html>'''
    file_output_path = html_output_path + html_name
    file = open(file_output_path,"w")
    file.write(text)
    file.close()
    logging.warning(",HTML File Created Hyperlink to the 360 image = " + path)


# In[ ]:


print('Attempting to acquire exif data and compress images...')
logging.warning(",Attempting to acquire exif data and compress images...")

# Loops through the parent directory, looks through every folder it finds unless the folder is called "Compressed".
def compress():
    global counter
    counter = 0
    csvdata = []
    missed_images_csv = []
    size = (600, 600) # Sets the resolution of thumbnails for 2D photos.
    for dirName, subdirList, fileList in os.walk(parent_dir):
        print(dirName)
        if "Compressed" not in dirName: 
            images = [file for file in os.listdir(dirName) if file.endswith(('jpg', 'png', 'JPG', 'PNG' ))] 
            for image in images:
                cutout = len (parent_dir)
                imagefilename = dirName[cutout:]
                imagefilename = parent_dir + imagefilename + "\\" + image # Sets the path and name of the image.
                img = Image.open(imagefilename) # Opens the image ready for exif extraction and Compression of the image.
                exifdata = img._getexif() # Grabs the Exif data from the image.
                logging.warning(",Opening file - " + image)
                
# Obtains the Exif data and converts it to a readable format
                def get_geotagging(exifdata):
                    if not exifdata:
                        print("No EXIF metadata found") # Provides a message if there is no Exif data for the image.
                        logging.warning(",No EXIF metadata found - " + image)
                    geotagging = {}
                    for (idx, tag) in TAGS.items():
                        if tag == 'GPSInfo':
                            if exifdata == None:
                                pass
                            elif idx not in exifdata:
                                print("No Geotagging found") # Provides a message if there is no Geotag data for the image.
                                logging.warning(",No Geotagging found - " + image)
                            else:
                                for (key, val) in GPSTAGS.items():
                                    if key in exifdata[idx]:
                                        geotagging[val] = exifdata[idx][key] # Separates the Geotags into readable items.

                    return geotagging
                geotags = get_geotagging(exifdata)
# Stores altitude, direction, latitude, and longitude Exif from the tags extrated earlier as variables.
                try:
                    altitude = geotags['GPSAltitude'] 
                except:
                    altitude = 0

                try:
                    direction = geotags['GPSImgDirection'] 
                except:
                    direction = ''

# Converts the Latitude and Longitude data from DMS format to Decimal format.
                try:
                    latitude = geotags['GPSLatitude']
                    latitude = float(latitude[0]) + float((latitude[1]) / 60) + float((latitude[2])/3600)
                    longitude = geotags['GPSLongitude']
                    longitude = float(longitude[0]) + float((longitude[1]) / 60) + float((longitude[2])/3600)

                    if geotags['GPSLatitudeRef'] == 'S':
                        latitude = -latitude
                    else: 
                        pass

                    if geotags['GPSLongitudeRef'] == 'W':
                        longitude = -longitude
                    else: 
                        pass
                except:
                    latitude = ''
                    longitude = ''
                    del latitude
                    del longitude
                    print("No Coordinates found") # Provides a message if there is no Coordinate data for the image.
                    logging.warning(",No Coordinates found - " + image)
                    no_geotags = "No Geotags"

# Extracts the Date and Time Tag from Exif.
                def get_labelled_exif(exifdata):
                    labelled = {}
                    for (key, val) in exifdata.items():
                        labelled[TAGS.get(key)] = val
                    return labelled
                
# Stores the Date/Time Exif data as a variable.
                try:
                    no_xmp = "Has XMP"
                    labelled = get_labelled_exif(exifdata)
                    timestamp = labelled['DateTime']
# Stores the original file location as a variable.
                    original = dirName + "\\" + image
# Stores the newly Compressed file location as a variable.
                    photo = dirName + '\\' + 'Compressed\Compressed_' + image
# Stores the newly Compressed filename as a variable.
                    photofile = 'Compressed_' + image
# Creates the path to the 360 file which is used in the html file to display the 360 image.
                    folder_check = dirName[cutout:]
                    folder_check = folder_check.replace("\\","/")
                    folder_check = folder_check[1:]
                    if folder_check == '':
                        pass
                    else:
                        folder_check = "/" + folder_check
                    imghtml = image[:-3] + 'html'
# Searches for XMP data attached to the photo.
                    xmp = str(img.applist)
                    img2d = "/Compressed/Compressed_" + image
# Checks if the image is a 360 photo by checking the XMP data.
                    if "equirectangular" in xmp:
                        xmp = True
                    else: 
                        xmp = False
# If the image is a 360, it saves the hyperlink to the html file as a variable.
                    if xmp == True:
                        web_link = ''
                        viewer = pano360 + "/" + imghtml
                        viewer_alt = ''
# if the image is 2D, it saves the hyperlink to both the original image and the compressed image as variables.
                    else:
                        web_link = website + alias + folder_check + img2d
                        viewer_alt = website + alias + folder_check + "/" +  image
                        viewer = ''
                except:
                    print("No XMP data to extract") # Provides a message if there is no XMP data for the image.
                    logging.warning(",No XMP data to extract - " + image)
                    no_xmp = "No XMP"
                    folder_check = dirName[cutout:]
                    folder_check = folder_check.replace("\\","/")
                    folder_check = folder_check[1:]
                    img2d = "/Compressed/Compressed_" + image
                    web_link = website + alias + folder_check + img2d
                    viewer_alt = website + alias + folder_check + "/" +  image
                    viewer = ''
                
# Turns the Exif and XMP data extracted as variables into rows and appends each one.
                try:
                    csvrows = np.array ([photo, photofile, dirName, altitude, direction, longitude, 
                                         latitude, timestamp, original, web_link, viewer, viewer_alt])
                    csvdata.append(csvrows)
                    counter = counter + 1
                except:
# Provides a final warning that the image will not appear in the CSV or SHP file as it has no discernable data.
                    img_dir = dirName + '\\'+ image
                    img_dir_split = os.path.join(','+dirName,','+image)
                    missed_images = np.array ([img_dir, dirName, image, no_geotags, no_xmp])
                    missed_images_csv.append(missed_images)
                    print("Photo not imported to SHP File  - No data to import!," + img_dir + img_dir_split) 
                    logging.warning(",Photo not imported to SHP File - No data to import!," + img_dir + img_dir_split) 
# Compresses the open image and saves it into the relevant 'compressed' folder                
                try:
                    img_name = ("Compressed_"+image)
                    output_comp = dirName+'\\Compressed'
                    output_path = os.path.join(output_comp, img_name)
# Attemps to preserve Exif data during compression.
                    try:
                        exif = img.info['exif']
                    except:
                        print("No Exif data to preserve.")
                        logging.warning(",No Exif data to preserve - " + image)
                    xmp = str(img.applist)
# 360 images are compressed using this method.
                    if "equirectangular" in xmp:
                        if os.path.isfile(output_path) == False: # Checks to see if the image is already compressed.
                            img.save(output_path, # Chooses where to save the image.
                            optimize=True,
                            quality=80, # Sets the quality of the compressed image.
                            exist_ok=True,
                            exif=exif) # Re-appends the exif data to the compressed image.
                            print(img_name + ' - 360 Image')
                            folder_check = dirName[cutout:]
                            folder_check = '/'.join(folder_check.split('\\'))
                            
# Sets the variables required to produce the html file.
                            html_link = website + alias + folder_check + '/Compressed/' + img_name
                            html_name = image[:-4] + '.html'
                            htmloutput(html_link, html_name)
                        else:
                            print(img_name+" - 360 Image - is already compressed!") 
                            logging.warning(",360 Image is already compressed - skipping " + img_name)
                            
# 2D Images are compressed and resized using this method.
                    else:
                        if os.path.isfile(output_path) == False: 
                            img.thumbnail(size) # Reduces the image resolution.
                            img.save(output_path, # Sets the output location for the image.
                            optimize=True,
                            quality=70, # Sets the quality of the Compressed image.
                            exist_ok=True,
                            exif=exif) # Re-appends the Exif data to the Compressed image.
                            print(img_name + ' - 2D Image')
                            
                        else:
                            print(img_name+" - 2D Image - is already compressed!") 
                            logging.warning(",2D Image is already compressed - skipping " + img_name) 
                            
                except OSError as error:
                    print(OSError)
                    logging.warning(OSError)
                    
# Sets the column headers for the CSV file.
            try:
                csvcolumns = np.array(['photo', 'file', 'directory', 'altitude', 'direction', 'longitude', 
                                       'latitude', 'timestamp', 'original', 'viewer-1', 'viewer-2', 'viewer-alt'])
            except:
                pass
# Saves the rows of data collected earlier into a CSV file. One row is created per image compressed.
    try:
        np.savetxt(csv_path,
                    csvdata, 
                    delimiter =", ",  
                    fmt ='%s',
                    newline='\n',
                    header = 'photo,' + 'file,' + 'directory,' + 'altitude,' + 'direction,' 
                    + 'longitude,' + 'latitude,' + 'timestamp,' + 'original,' + 'viewer-1,' + 'viewer-2,' + 'viewer-alt',
                    comments = '')
        logging.warning(",CSV file Created!") 
    except:
        pass
    try:
        np.savetxt(missed_images_csv_path,
                    missed_images_csv,
                    delimiter = ", ",
                    fmt ='%s',
                    newline='\n',
                    header = 'FullPath,' + 'Directory,' +  'FileName,' + 'GeotagData?,' + 'XMPData?',
                    comments ='')
        logging.warning(",Missed Images CSV file created! Located here - " + missed_images_csv_path)
    except:
        print("Creating Missed Images CSV file failed.")
        logging.warning(",Creating Missed Images CSV file failed.")
    return counter

compress ()
print('Exif data acquired and compression successful!')
logging.warning(",Exif data acquired and compression successful!") 


# In[ ]:


print('Attempting to create SHP file...')
logging.warning(",Attempting to create SHP file...") 
# Sets the driver for creating the correct format for the SHP file.
DriverName = "ESRI Shapefile"      # e.g.: GeoJSON, ESRI Shapefile
FileName = shp_file_outpath
CSVName = csv_path
driver = ogr.GetDriverByName(DriverName)
# Checks if a SHP file with the same name already exists at the output location, if it does, it tries to delete it.
# This will fail if the SHP file is currently in use by either QGIS or Lizmap.
# Close any QGIS project you have open which is using this file.
# Open task manager and close any instances of "qgis_mapserv.fcgi.exe".
if os.path.exists(FileName):
     driver.DeleteDataSource(FileName)


# In[ ]:


# Sets the source file for opening and editing.
data_source = driver.CreateDataSource(FileName)

# Create the spatial reference, WGS84
srs = osr.SpatialReference()
srs.ImportFromEPSG(4326)

# Create the layer
layer = data_source.CreateLayer("photos", srs, ogr.wkbPoint)

# Add the fields we're interested in, these must match the CSV rows we created earlier.
field_photo = ogr.FieldDefn("photo", ogr.OFTString)
field_photo.SetWidth(200)
layer.CreateField(field_photo)

field_filename = ogr.FieldDefn("file", ogr.OFTString)
field_filename.SetWidth(100)
layer.CreateField(field_filename)

field_directory = ogr.FieldDefn("directory", ogr.OFTString)
field_directory.SetWidth(200)
layer.CreateField(field_directory)

layer.CreateField(ogr.FieldDefn("altitude", ogr.OFTReal))
layer.CreateField(ogr.FieldDefn("direction", ogr.OFTReal))
layer.CreateField(ogr.FieldDefn("longitude", ogr.OFTReal))
layer.CreateField(ogr.FieldDefn("latitude", ogr.OFTReal))
layer.CreateField(ogr.FieldDefn("timestamp", ogr.OFTString))

field_directory = ogr.FieldDefn("original", ogr.OFTString)
field_directory.SetWidth(200)
layer.CreateField(field_directory)

field_directory = ogr.FieldDefn("viewer-1", ogr.OFTString)
field_directory.SetWidth(200)
layer.CreateField(field_directory)

field_directory = ogr.FieldDefn("viewer-2", ogr.OFTString)
field_directory.SetWidth(200)
layer.CreateField(field_directory)

field_directory = ogr.FieldDefn("viewer-alt", ogr.OFTString)
field_directory.SetWidth(200)
layer.CreateField(field_directory)

# Opens the CSV file we created earlier.
with open(CSVName, newline='\n') as csvfile:
    reader = csv.DictReader(csvfile)
# Process the text file and add the attributes and features to the shapefile.
    for row in reader:
# Create the feature.
        feature = ogr.Feature(layer.GetLayerDefn())
# Set the attributes using the values from the CSV file.
        feature.SetField("photo", row['photo'])
        feature.SetField("file", row['file'])
        feature.SetField("directory", row['directory'])
        feature.SetField("altitude", row['altitude'])
        feature.SetField("direction", row['direction'])
        feature.SetField("longitude", row['longitude'])
        feature.SetField("latitude", row['latitude'])
        feature.SetField("timestamp", row['timestamp'])
        feature.SetField("original", row['original'])
        feature.SetField("viewer-1", row['viewer-1'])
        feature.SetField("viewer-2", row['viewer-2'])
        feature.SetField("viewer-alt", row['viewer-alt'])

# create the WKT for the feature using Python string formatting
        wkt = "POINT(%f %f)" %  (float(row['longitude']) , float(row['latitude']))
# Create the point from the Well Known Txt
        point = ogr.CreateGeometryFromWkt(wkt)
# Set the feature geometry using the point
        feature.SetGeometry(point)
# Create the feature in the layer (shapefile)
        layer.CreateFeature(feature)
# De-reference the feature
        feature = None

# Closes the SHP file, ready for use.
data_source = None


# In[ ]:


print('SHP file created!')
logging.warning(",SHP file created!") 
print('It took', time.time()-tstart, 'seconds to compress ', counter, ' images.')
time = str(time.time()-tstart)
logging.warning(',It took ' + time + ' seconds to compress ' + counter + ' images.') 
print('You can find additional log details here : E:\webserver\Python Script Logs\\any-compress')

# In[ ]:




