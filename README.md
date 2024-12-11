# Medusa
Internet Archive streamer for XBMC. 

![1](release/default.tbn)

Requires the latest version of XBMC from Xbins (as it has crucial TLS/SSL updates that allow this script to work). Sources are NOT provided (outside of one public domain movie source) and must be input manually!

![1](screenshots/1.bmp)
![2](screenshots/2.bmp)
![3](screenshots/3.bmp)

## How To Use:
- Download latest release file, or "release" folder from the repository (delete update.zip if you do!).
- Extract the .zip file, edit "default.py" and modify the "CATEGORY_COLLECTIONS =" section to point to the Internet Archive collection(s) of your choice! Just make a copy of the line below and modify it as needed, making sure the last entry in a category does not end with a comma!
- Copy the "Medusa" folder to Q:/plugins/video
- Run the add-on and enjoy!

## Issues:
- Some videos WILL crash your Xbox if they're too high-quality. This isn't the fault of the script, the Xbox is very picky about what files it's fine with (64MB and a Pentium III isn't a lot to work with). Look for specifically 360p/480p files where available.
- You tell me.

## TODO:
- Implement the ability to search for and add collections on the fly.
- Improve media streaming a bit.
- Implement better filename sanitization
- Implement some sort of login system so access-locked files can be downloaded.
- Incorporate update script.

## Disclaimer:
- The Internet Archive is a vast archive of many files, tons of which are legal to download! Make sure you follow the copyright laws of your region while downloading from Internet Archive sources. Support will not be given for anyone trying to use this utility for blatant piracy. 
