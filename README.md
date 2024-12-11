# Medusa
Internet Archive streamer for XBMC. 

Requires the latest version of XBMC from Xbins (as it has crucial TLS/SSL updates that allow this script to work). Sources are NOT provided and must be input manually!

![1](screenshots/1.bmp)
![2](screenshots/2.bmp)
![3](screenshots/3.bmp)

## How To Use:
- Download latest release file, or "release" folder from the repository.
- Extract the .zip file, edit "default.py" to point "COLLECTION_URL" to the Internet Archive collection of your choice 
- Copy the "Medusa" folder to Q:/plugins/video
- Run the add-on and enjoy!

## Issues:
- Some files with absurdly long file names and multiple special characters (like "4 Game in One - Ice Hockey, Phantom UFO, Spy Vs. Spy, Cosmic Avenger (1983) (Bit Corporation) (PAL).bin") will crash the script. Sanitization function definitely needs a bit of work.
- You tell me.

## TODO:
- Improve media streaming a bit.
- Implement better filename sanitization
- Implement scanning from multiple collections at the same time.
- Implement some sort of login system so access-locked files can be downloaded.

## Disclaimer:
- The Internet Archive is a vast archive of many files, tons of which are legal to download! Make sure you follow the copyright laws of your region while downloading from Internet Archive sources. Support will not be given for anyone trying to use this utility for blatant piracy. 
