import sys
import xbmc
import xbmcgui
import xbmcplugin
import requests
import urllib
import urlparse
import os
import time
import json
import re

ADDON_NAME = "Medusa"
BASE_URL = "https://archive.org/details/"  # Base URL for Internet Archive collections
DOWNLOAD_DIR = "F:/Medusa"  # Directory to save downloaded files
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

def sanitize_filename(filename, part_number=0):
    """Sanitize the filename to comply with FATX standards."""
    import re
    sanitized = re.sub(r'[<>:"/\\|?*,]', '', filename)
    max_length = 42
    if part_number > 0:
        extension_length = 4  # ".001" etc.
        max_length -= extension_length
    if len(sanitized) > max_length:
        name, ext = os.path.splitext(sanitized)
        sanitized = name[:max_length - len(ext)] + ext
    if part_number > 0:
        sanitized = "{}.{:03d}".format(sanitized, part_number)
    return sanitized

def download_file(url, filename):
    """Download the file to the DOWNLOAD_DIR with a progress bar and speed display."""
    try:
        # Sanitize the filename
        filename = sanitize_filename(filename)
        
        # Create the download directory if it doesn't exist
        if not os.path.exists(DOWNLOAD_DIR):
            os.makedirs(DOWNLOAD_DIR)

        # Initialize the progress dialog
        progress_dialog = xbmcgui.DialogProgress()
        progress_dialog.create(filename, "Downloading " + filename)

        # Start downloading regardless of file size
        response = requests.head(url, timeout=30, allow_redirects=True)
        if response.status_code != 200:
            xbmcgui.Dialog().ok(ADDON_NAME, "Failed to retrieve the file: HTTP {}".format(response.status_code))
            return

        # Get total file size from Content-Length header, if available
        total_size = int(response.headers.get('Content-Length', 0))
        part_size = 4294967296  # 4 GB
        part_number = 1
        downloaded_size = 0
        start_time = time.time()

        if total_size > part_size:
            # File size is greater than 4GB, split into parts
            while downloaded_size < total_size:
                headers = {
                    'Range': 'bytes={}-{}'.format(downloaded_size, min(downloaded_size + part_size - 1, total_size - 1))
                }
                response = requests.get(url, headers=headers, stream=True, timeout=30)
                if response.status_code not in (200, 206):
                    xbmcgui.Dialog().ok(ADDON_NAME, "Failed to retrieve the file part: HTTP {}".format(response.status_code))
                    return

                part_filename = sanitize_filename(filename, part_number)
                file_path = os.path.join(DOWNLOAD_DIR, part_filename)
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=4096 * 1024):  # 4 MB chunks
                        if chunk:
                            f.write(chunk)
                            downloaded_size += len(chunk)

                            # Calculate elapsed time and speed
                            elapsed_time = time.time() - start_time
                            if elapsed_time > 0:
                                speed_kbps = (downloaded_size / elapsed_time) / 1024  # Convert to Kbps
                                progress = int((downloaded_size / float(total_size)) * 100)
                                mb_downloaded = downloaded_size / (1024.0 * 1024.0)  # Convert to MB

                                # Update progress dialog
                                progress_dialog.update(
                                    progress,
                                    "Downloading: {:.2f} MB".format(mb_downloaded),
                                    "Speed: {:.2f} Kbps".format(speed_kbps),
                                    "Progress: {}%".format(progress)
                                )

                            if progress_dialog.iscanceled():
                                progress_dialog.close()
                                xbmcgui.Dialog().ok("Cancelled", "Download cancelled")
                                return

                part_number += 1

            progress_dialog.close()
            xbmcgui.Dialog().ok("Download Complete", "The file has been downloaded in {} parts.".format(part_number - 1))
        else:
            # File size is less than 4GB, download in one go
            response = requests.get(url, stream=True, timeout=30)
            if response.status_code != 200:
                xbmcgui.Dialog().ok(ADDON_NAME, "Failed to retrieve the file: HTTP {}".format(response.status_code))
                return

            file_path = os.path.join(DOWNLOAD_DIR, filename)
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=4096 * 1024):  # 4 MB chunks
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)

                        # Calculate elapsed time and speed
                        elapsed_time = time.time() - start_time
                        if elapsed_time > 0:
                            speed_kbps = (downloaded_size / elapsed_time) / 1024  # Convert to Kbps
                            progress = int((downloaded_size / float(total_size)) * 100)
                            mb_downloaded = downloaded_size / (1024.0 * 1024.0)  # Convert to MB

                            # Update progress dialog
                            progress_dialog.update(
                                progress,
                                "Downloading: {:.2f} MB".format(mb_downloaded),
                                "Speed: {:.2f} Kbps".format(speed_kbps),
                                "Progress: {}%".format(progress)
                            )

                        if progress_dialog.iscanceled():
                            progress_dialog.close()
                            xbmcgui.Dialog().ok("Cancelled", "Download cancelled")
                            return

            progress_dialog.close()
            xbmcgui.Dialog().ok("Download Complete", "The file has been downloaded: {}".format(filename))

    except Exception as e:
        xbmcgui.Dialog().ok("Download Error", "Error downloading file: {}".format(str(e)))


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
    for category in sorted(CATEGORY_ORDER):
        list_item = xbmcgui.ListItem(label=category)
        list_item.setInfo('video', {'title': category})
        query = urllib.urlencode({'category': category})
        url_with_query = "{0}?{1}".format(sys.argv[0], query)
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url_with_query, listitem=list_item, isFolder=True)

    xbmcplugin.endOfDirectory(addon_handle)
