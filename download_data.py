import os
import requests
from zipfile import ZipFile
from datetime import datetime
import shutil

'''
Script handle the download of MovieLens data since they do not have an API to extract the data more efficiently.
'''

# URL of the zip file
zip_url = "https://files.grouplens.org/datasets/movielens/ml-25m.zip"

# Destination folder for downloading and extracting
destination_folder = "movielens-data"

# Check if the destination folder exists
if os.path.exists(destination_folder):
    # Rename existing folder to movielens-data-deprecated-YYYY-MM-DD
    timestamp = datetime.now().strftime("%Y-%m-%d")
    deprecated_folder_name = f"movielens-data-deprecated-{timestamp}"

    # Use shutil.move to perform a recursive move (replace)
    shutil.move(destination_folder, deprecated_folder_name)
    print(f"Renamed existing {destination_folder} to {deprecated_folder_name}")

# Create the destination folder
os.makedirs(destination_folder)

# Download the zip file
response = requests.get(zip_url)
zip_filename = os.path.join(destination_folder, "ml-25m.zip")

with open(zip_filename, "wb") as zip_file:
    zip_file.write(response.content)

# Unzip the file
with ZipFile(zip_filename, "r") as zip_ref:
    zip_ref.extractall(destination_folder)

# Move the contents of ml-25m folder to destination folder
extracted_folder = os.path.join(destination_folder, "ml-25m")
for item in os.listdir(extracted_folder):
    s = os.path.join(extracted_folder, item)
    d = os.path.join(destination_folder, item)
    shutil.move(s, d)

# Delete the ml-25m folder
os.rmdir(extracted_folder)

# Delete the zip file
os.remove(zip_filename)
print(f"Downloaded and moved to {destination_folder}, zip file deleted.")