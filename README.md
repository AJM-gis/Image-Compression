# Image-Compression-Script

# The problem: 
- Employees working on a data collection exercise drop photos onto a server. They also create their own individual folder structures, it is not possible to predict what folder structure they will use. They will also drop other types of files into these folders.
- Client wishes to see the data displayed on an interactive mapping platform which shows the location of the images and is capable of displaying them within the platform.

# The Solution:
A Python Script which is capable of grabbing all of the image files from a directory (as well as any Sub-Directories), and then creates a SHP file which contains relevant data regarding each image. This SHP file is then utilised by QGIS Server and a web-client to display the images and their locations as a point dataset.

# Script Overview
Prepares 2D and 360 (photosphere) images for use within a Web-GIS platform:
- Extracts EXIF, and XMP data from images.
- Converts these data into readable formats and saves them into variables.
- Differentiates between 2D photos and 360 photos.
- Compresses the images, maintaining quality but vastly reducing image size (necessary for a smoother user experience).
- Creates a SHP file which stores useful EXIF metadata relating to each image.
- Creates a column within the SHP file which points to where the Compressed image is stored so that it can be linked to in HTML.
- Creates a unique HTML file for each 360 image, which contains a "Panolens" JavaScript library that is capable of displaying Photosphere images.

Note: 
This Script was designed with a specific server structure in mind and is most easily used when combining it with a "Lizmap" Web-GIS platform. Small modifications can be made to alter the Script to suit your needs.
