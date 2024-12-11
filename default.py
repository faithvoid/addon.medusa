import sys
import xbmc
import xbmcgui
import xbmcplugin
import requests
import urllib
import urlparse

ADDON_NAME = "Medusa"
COLLECTION_URL = ""  # Replace with your collection URL

MEDIA_EXTENSIONS = {".mp4", ".mp3", ".avi", ".mkv", ".wav", ".flac", ".mov", ".mpg"}  # Add more as needed

def fetch_collection_metadata():
    """Fetch metadata for the collection from the URL."""
    collection_id = COLLECTION_URL.split("/")[-1]
    api_url = "https://archive.org/metadata/{}".format(collection_id)
    
    response = requests.get(api_url)
    if response.status_code == 200:
        return response.json()
    else:
        xbmcgui.Dialog().ok(ADDON_NAME, "Failed to fetch collection metadata.")
        return None

def list_files():
    """List the files in the collection and provide options to stream them."""
    metadata = fetch_collection_metadata()
    if not metadata:
        return
    
    files = metadata.get("files", [])
    if not files:
        xbmcgui.Dialog().ok(ADDON_NAME, "No files found in the collection.")
        return
    
    # Filter the files by media extensions
    file_names = [file["name"] for file in files if "name" in file and file["name"].lower().endswith(tuple(MEDIA_EXTENSIONS))]
    
    if not file_names:
        xbmcgui.Dialog().ok(ADDON_NAME, "No media files found in the collection.")
        return

    # Add the video files to the list for selection
    for index, file_name in enumerate(file_names):
        # Encode the file_name to UTF-8 to handle special characters
        encoded_file_name = urllib.quote(file_name.encode('utf-8'))
        url = "https://archive.org/download/{}/{}".format(metadata['metadata']['identifier'], encoded_file_name)

        list_item = xbmcgui.ListItem(label=file_name)
        list_item.setInfo('video', {'title': file_name})
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=list_item, isFolder=False)

    # End the listing and refresh the content
    xbmcplugin.endOfDirectory(addon_handle)

def play_video(url):
    """Play the selected video URL."""
    encoded_url = urllib.quote(url, safe=':/')
    xbmc.Player().play(encoded_url)

# Initialize the addon handle (required for XBMC plugin)
addon_handle = int(sys.argv[1])

# Get the query string from the URL
parsed_url = urlparse.urlparse(sys.argv[2])
params = urlparse.parse_qs(parsed_url.query)

if 'url' in params:
    # If a 'url' parameter is found, play the selected video
    play_video(params['url'][0])
else:
    # Otherwise, list the available video files
    list_files()
