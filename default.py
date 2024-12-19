import sys
import xbmc
import xbmcgui
import xbmcplugin
import requests
import urllib
import urlparse
import json

ADDON_NAME = "Medusa"
BASE_URL = "https://archive.org/details/"  # Base URL for Internet Archive collections
COLLECTIONS_FILE = "Q:/plugins/video/Medusa/collections.txt"  # File containing collections data

def read_collections_from_file(filename):
    """Read collections from a file and return a dictionary and a list of categories."""
    if not os.path.exists(filename):
        xbmcgui.Dialog().ok(ADDON_NAME, "Collections file not found: {}".format(filename))
        return {}, []

    try:
        with open(filename, 'r') as file:
            collections = json.load(file)
        categories = list(collections.keys())
        return collections, categories
    except Exception as e:
        xbmcgui.Dialog().ok(ADDON_NAME, "Failed to read collections file: {}".format(str(e)))
        return {}, []

# Read collections and category order from the file
CATEGORY_COLLECTIONS, CATEGORY_ORDER = read_collections_from_file(COLLECTIONS_FILE)

def fetch_collection_metadata(collection_id):
    """Fetch metadata for a collection from the Internet Archive."""
    api_url = "https://archive.org/metadata/{0}".format(collection_id)
    try:
        response = requests.get(api_url)
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.RequestException as e:
        xbmcgui.Dialog().ok(ADDON_NAME, "Failed to fetch metadata for {0}: {1}".format(collection_id, str(e)))
    return None

def fetch_collection_metadata(collection_id):
    """Fetch metadata for a collection from the Internet Archive."""
    api_url = "https://archive.org/metadata/{0}".format(collection_id)
    try:
        response = requests.get(api_url)
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.RequestException as e:
        xbmcgui.Dialog().ok(ADDON_NAME, "Failed to fetch metadata for {0}: {1}".format(collection_id, str(e)))
    return None

def fetch_page_metadata(page_id):
    """Fetch metadata for a collection detail page which lists other collections."""
    api_url = "https://archive.org/details/{0}".format(page_id)
    try:
        response = requests.get(api_url)
        if response.status_code == 200:
            return response.text  # Return raw HTML to parse for sub-collections
    except requests.exceptions.RequestException as e:
        xbmcgui.Dialog().ok(ADDON_NAME, "Failed to fetch page details for {0}: {1}".format(page_id, str(e)))
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

def download_file(url, filename):
    """Download the file to the F:/Media directory with a progress bar and speed display."""
    try:
        # Create the download directory if it doesn't exist
        if not os.path.exists(DOWNLOAD_DIR):
            os.makedirs(DOWNLOAD_DIR)

        # Use requests to get the file, with stream=True to download it in chunks
        response = requests.get(url, stream=True)

        if response.status_code == 200:
            # Get total file size from Content-Length header
            total_size = int(response.headers.get('Content-Length', 0))
            file_path = os.path.join(DOWNLOAD_DIR, filename)
            
            # Open the file to write the downloaded content in chunks
            with open(file_path, 'wb') as f:
                downloaded_size = 0
                chunk_size = 8192  # 8 KB chunks
                start_time = time.time()  # Track time when download starts
                last_update_time = start_time  # Time of the last progress update
                last_speed_kbps = 0  # Last speed value to avoid showing "0.0 kBps"

                # Initialize the progress dialog
                progress_dialog = xbmcgui.DialogProgress()
                progress_dialog.create("Downloading", "Starting download...", "", "")

                # Download the file in chunks
                bytes_this_second = 0  # To track the number of bytes downloaded in the last second
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        # Write the chunk to the file
                        f.write(chunk)
                        downloaded_size += len(chunk)  # Update downloaded size
                        bytes_this_second += len(chunk)  # Track bytes downloaded in the last second

                        # Calculate elapsed time for current chunk download
                        current_time = time.time()
                        elapsed_time = current_time - last_update_time

                        # Update speed once per second (speed in kBps)
                        if elapsed_time >= 1:  # Only update the speed once per second
                            speed_kbps = bytes_this_second / 1024  # Convert bytes to kilobytes
                            bytes_this_second = 0  # Reset bytes this second counter
                            last_speed_kbps = speed_kbps
                            last_update_time = current_time  # Update last update time

                        # Update progress bar (convert to MB)
                        downloaded_mb = downloaded_size / (1024 * 1024)  # Convert to MB
                        total_mb = total_size / (1024 * 1024)  # Convert to MB
                        # Calculate percentage (ensure it's an integer)
                        percentage = int((downloaded_size / total_size) * 100) if total_size else 0

                        # Display download speed on a separate line only if speed is not 0 or has changed
                        if last_speed_kbps > 0:  # Only show speed if it is greater than 0
                            progress_dialog.update(percentage, 
                                                   "Downloading: {} MB of {} MB".format(downloaded_mb, total_mb),
                                                   "",
                                                   "Speed: {} KBps".format(last_speed_kbps))
                        else:
                            progress_dialog.update(percentage, 
                                                   "Downloading: {} MB of {} MB".format(downloaded_mb, total_mb),
                                                   "",
                                                   "")  # Don't display speed if it's zero

                        # Check if the user cancelled the download
                        if progress_dialog.iscanceled():
                            xbmcgui.Dialog().ok("Download Cancelled", "The download was cancelled.")
                            return

                progress_dialog.close()  # Close the progress dialog after download is complete
            xbmcgui.Dialog().ok("Download Complete", "The file has been downloaded: {0}".format(filename))
        else:
            xbmcgui.Dialog().ok("Download Failed", "Failed to download the file from: {0}".format(url))

    except Exception as e:
        xbmcgui.Dialog().ok("Download Error", "Error downloading file: {0}".format(str(e)))

def list_files(collection_id, folder=""):
    """
    List files and subfolders within a selected collection or specific folder.
    """
    metadata = fetch_collection_metadata(collection_id)
    if not metadata:
        return

    files = metadata.get("files", [])
    if not files:
        xbmcgui.Dialog().ok(ADDON_NAME, "No files found in this collection.")
        return

    # Prepare lists for subfolders and files
    subfolders = set()
    current_files = []

    # Process each file in the metadata
    for file in files:
        if "name" not in file:
            continue

        file_path = file["name"]
        if not file_path.startswith(folder):  # Skip files outside the current folder
            continue

        relative_path = file_path[len(folder):].lstrip("/")
        if "/" in relative_path:  # Subfolder detected
            subfolder = relative_path.split("/")[0]
            subfolders.add(subfolder)
        elif relative_path:  # File in the current folder
            current_files.append(file_path)

    # List subfolders first
    for subfolder in sorted(subfolders):
        list_item = xbmcgui.ListItem(label=subfolder)
        list_item.setInfo('video', {'title': subfolder})
        next_folder = "/".join([folder, subfolder]).strip('/')
        query = urllib.urlencode({'collection_id': collection_id, 'folder': next_folder})
        url_with_query = "{0}?{1}".format(sys.argv[0], query)
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url_with_query, listitem=list_item, isFolder=True)

    # List files in the current folder
    for file_path in sorted(current_files):
        file_name = file_path.split("/")[-1]

        # Construct the full URL for the file
        encoded_path = urllib.quote(file_path.encode('utf-8'), safe='/')
        url = "https://archive.org/download/{0}/{1}".format(collection_id, encoded_path)

        # Prepare the list item for the file
        list_item = xbmcgui.ListItem(label=file_name)
        list_item.setInfo('video', {'title': file_name})

        # Add a context menu item for downloading the file
        context_menu_items = [
            ("Download", "RunPlugin({0}?action=download&url={1}&filename={2})".format(sys.argv[0], urllib.quote(url.encode('utf-8')), urllib.quote(file_name.encode('utf-8'))))
        ]
        list_item.addContextMenuItems(context_menu_items)

        # Add the file to the directory listing
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=list_item, isFolder=False)

    # Finalize directory
    xbmcplugin.endOfDirectory(addon_handle)



def play_video(url):
    """Play the selected video URL."""
    encoded_url = urllib.quote(url, safe=':/')
    xbmc.Player().play(encoded_url)


def handle_download_action():
    """Handle the download action when the context menu option is selected."""
    url = params.get('url', [None])[0]
    filename = params.get('filename', [None])[0]
    if url and filename:
        download_file(url, filename)
    else:
        xbmcgui.Dialog().ok(ADDON_NAME, "Download failed: Invalid URL or filename.")

# Initialize the addon handle (required for XBMC plugin)
addon_handle = int(sys.argv[1])

# Get the query string from the URL
parsed_url = urlparse.urlparse(sys.argv[2])
params = urlparse.parse_qs(parsed_url.query)

# Check for download action
if 'action' in params and params['action'][0] == 'download':
    handle_download_action()
elif 'collection_id' in params and 'folder' in params:
    list_files(params['collection_id'][0], params['folder'][0])
elif 'collection_id' in params:
    list_files(params['collection_id'][0])
elif 'category' in params:
    list_collections(params['category'][0])
else:
    # Display available categories
    for category in CATEGORY_ORDER:
        list_item = xbmcgui.ListItem(label=category)
        list_item.setInfo('video', {'title': category})
        query = urllib.urlencode({'category': category})
        url_with_query = "{0}?{1}".format(sys.argv[0], query)
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url_with_query, listitem=list_item, isFolder=True)

    xbmcplugin.endOfDirectory(addon_handle)
