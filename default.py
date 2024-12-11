import sys
import xbmc
import xbmcgui
import xbmcplugin
import requests
import urllib
import urlparse

ADDON_NAME = "Medusa"
BASE_URL = "https://archive.org/details/"  # Base URL for Internet Archive collections

MEDIA_EXTENSIONS = {".mp4", ".mp3", ".avi", ".mkv", ".wav", ".flac", ".mov", ".mpg"}

# Define the collections for each category
CATEGORY_COLLECTIONS = {
    "Television": [
        {"name": "N/A", "id": "N/A"}
    ],
    "Cartoons": [
        {"name": "N/A", "id": "N/A"}
    ],
    "Anime": [
        {"name": "N/A", "id": "N/A"}
    ],
    "Movies": [
        {"name": "Public Domain Movies", "id": "publicmovies212"}
    ],
    "Other": [
        {"name": "N/A", "id": "N/A"}
    ]
}

# List categories in the desired order
CATEGORY_ORDER = ["Television", "Cartoons", "Anime", "Movies", "Other"]

def fetch_collection_metadata(collection_id):
    """Fetch metadata for a collection from the Internet Archive."""
    api_url = "https://archive.org/metadata/{0}".format(collection_id)
    response = requests.get(api_url)
    if response.status_code == 200:
        return response.json()
    else:
        xbmcgui.Dialog().ok(ADDON_NAME, "Failed to fetch metadata for {0}.".format(collection_id))
        return None

def list_collections(category):
    """List collections for a given category."""
    collections = CATEGORY_COLLECTIONS.get(category, [])
    
    if not collections:
        xbmcgui.Dialog().ok(ADDON_NAME, "No collections found in this category.")
        return

    for collection in collections:
        list_item = xbmcgui.ListItem(label=collection["name"])
        list_item.setInfo('video', {'title': collection["name"]})

        # Format the URL to pass the collection ID
        query = urllib.urlencode({'collection_id': collection['id']})
        url_with_query = "{0}?{1}".format(sys.argv[0], query)

        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url_with_query, listitem=list_item, isFolder=True)

    xbmcplugin.endOfDirectory(addon_handle)

def list_files(collection_id):
    """List files within a selected collection and provide options to stream them."""
    metadata = fetch_collection_metadata(collection_id)
    if not metadata:
        return
    
    files = metadata.get("files", [])
    if not files:
        xbmcgui.Dialog().ok(ADDON_NAME, "No files found in this collection.")
        return
    
    # Filter the files by media extensions
    file_names = [file["name"] for file in files if "name" in file and file["name"].lower().endswith(tuple(MEDIA_EXTENSIONS))]
    
    if not file_names:
        xbmcgui.Dialog().ok(ADDON_NAME, "No media files found in this collection.")
        return

    # Add the video files to the list for selection
    for file_name in file_names:
        encoded_file_name = urllib.quote(file_name.encode('utf-8'))
        url = "https://archive.org/download/{0}/{1}".format(collection_id, encoded_file_name)

        list_item = xbmcgui.ListItem(label=file_name)
        list_item.setInfo('video', {'title': file_name})
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=list_item, isFolder=False)

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
elif 'collection_id' in params:
    # If a 'collection_id' is provided, list files in that collection
    list_files(params['collection_id'][0])
elif 'category' in params:
    # If a 'category' parameter is provided, list collections in that category
    list_collections(params['category'][0])
else:
    # Otherwise, list the available categories in the static order defined in CATEGORY_ORDER
    for category in CATEGORY_ORDER:
        list_item = xbmcgui.ListItem(label=category)
        list_item.setInfo('video', {'title': category})

        # Format the URL to pass the category as a query parameter
        query = urllib.urlencode({'category': category})
        url_with_query = "{0}?{1}".format(sys.argv[0], query)

        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url_with_query, listitem=list_item, isFolder=True)

    xbmcplugin.endOfDirectory(addon_handle)
