import shutil
import os

source = 'chambres'
destination = 'media/chambres'

if not os.path.exists('media'):
    os.makedirs('media')

if os.path.exists(source):
    if os.path.exists(destination):
        print(f"Destination {destination} already exists. Merging...")
        for file in os.listdir(source):
            shutil.move(os.path.join(source, file), destination)
        os.rmdir(source)
    else:
        shutil.move(source, destination)
    print("Moved successfully.")
else:
    print("Source directory 'chambres' not found.")
