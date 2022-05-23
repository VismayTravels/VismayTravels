from selenium import webdriver  # So we can webscrape
from selenium.webdriver.common.by import By
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
#from selenium.webdriver.chrome.options import Options
from os import walk,path,remove,listdir
from zipfile import ZipFile
from PIL import Image
from pathlib import Path
import time                     # So we can delay loading
import shutil

'''
=================================== PARAMS ===================================
    downloads_path      : Set this equal to your downloads folder path.
    compressed_zip_name : Set this equal to the name of the zip from https://imagecompressor.com/. This could change in the future...
    compression_dir     : Set this equal to the local path for the working post-compression directory
    conversion_dir      : Set this equal to the local path for the working post-conversion directory
'''
downloads_path = 'C:/Users/lucas/Downloads'
compressed_zip_name = 'C:/Users/lucas/Downloads/imagecompressor.zip'
compression_dir = './post_compression'
conversion_dir = './post_conversion'
pre_process_dir = './pics_to_compress'
smallest_dir = './maximally_minimized'

'''
=================================== FUNCTIONS ===================================
'''
def drag_and_drop_file(drop_target, path):
    JS_DROP_FILE = """
    var target = arguments[0],
        offsetX = arguments[1],
        offsetY = arguments[2],
        document = target.ownerDocument || document,
        window = document.defaultView || window;

    var input = document.createElement('INPUT');
    input.type = 'file';
    input.onchange = function () {
      var rect = target.getBoundingClientRect(),
          x = rect.left + (offsetX || (rect.width >> 1)),
          y = rect.top + (offsetY || (rect.height >> 1)),
          dataTransfer = { files: this.files };

      ['dragenter', 'dragover', 'drop'].forEach(function (name) {
        var evt = document.createEvent('MouseEvent');
        evt.initMouseEvent(name, !0, !0, window, 0, 0, 0, x, y, !1, !1, !1, !1, 0, null);
        evt.dataTransfer = dataTransfer;
        target.dispatchEvent(evt);
      });

      setTimeout(function () { document.body.removeChild(input); }, 25);
    };
    document.body.appendChild(input);
    return input;
    """
    # The injection script

    # Use the injection script to simulate a drag and drop
    driver = drop_target.parent
    file_input = driver.execute_script(JS_DROP_FILE, drop_target, 0, 0)
    file_input.send_keys(path)

def convert_to_webp(source, dest):
    """Convert image to WebP.

    Args:
        source (pathlib.Path): Path to source image

    Returns:
        pathlib.Path: path to new image
    """
    destination = Path(dest + '/' + source).with_suffix(".webp")
    image = Image.open(compression_dir + '/' + source)  # Open image
    image.save(destination, format="webp")  # Convert image to webp
    return destination

def chunker(seq, size):
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))

'''
=================================== IMG COMPRESSION ===================================
'''
web = webdriver.Chrome()        # The Chrome Driver
#web.get('https://imagecompressor.com/')

# Empty the working directories
for f in listdir(compression_dir):
    remove(path.join(compression_dir, f))

for f in listdir(conversion_dir):
    remove(path.join(conversion_dir, f))


# XPATHS for https://imagecompressor.com/ :
drag_and_drop = '//*[@id="app"]/section[1]/div[2]/div[2]'
download_all = '//*[@id="app"]/section[1]/div[3]/button'
# Try with JS injection


dir_path = path.abspath(pre_process_dir) 
files = next(walk(pre_process_dir), (None, None, []))[2]  # [] if no file

print('Uploading the pictures to https://imagecompressor.com/, please wait...')
#drag_drop = web.find_element(By.XPATH, drag_and_drop)
for group in chunker(files, 20):
    web.get('https://imagecompressor.com/')
    drag_drop = web.find_element(By.XPATH, drag_and_drop)
    for file in group:
        drag_and_drop_file(drag_drop, path.join(dir_path, file))

    print('Waiting for the compression to occur, please wait...')
    # Wait until all have finished processing so that you can download them automatically:
    download_btn = WebDriverWait(web, 500).until(
    EC.element_to_be_clickable((By.XPATH, download_all)))
    download_btn.click();

    # Wait until the zip is done downloading
    print('Waiting for the zip to download, please wait...')
    while not path.exists(compressed_zip_name):
        time.sleep(1)

    if path.isfile(compressed_zip_name):
        print('Compressed images downloaded as ' + compressed_zip_name)
        
        # extract file
        print('Extracting compressed images to ./post_compression...')
    
        # Extract all the contents of zip file in different directory
        with ZipFile(compressed_zip_name, 'r') as zipObj:
            zipObj.extractall(compression_dir)

        # delete zip
        print('Deleting the zip...')
        remove(compressed_zip_name)

    else:
        raise ValueError("%s isn't a file!" % compressed_zip_name)

    # Now, convert the images to the webp type
    print('Converting the compressed images to webp type, please wait...')
    files = next(walk(compression_dir), (None, None, []))[2]  # [] if no file
    for file in files:
        convert_to_webp(file, conversion_dir)

    # Determine the Maximally Minimized Versions & Write out:
    files = next(walk(compression_dir), (None, None, []))[2]  # [] if no file
    for file in files:
        no_ext = path.splitext(file)[0]
        compressed_size = path.getsize(path.join(compression_dir,file))
        webp_compressed_size = path.getsize(path.join(conversion_dir,no_ext + '.webp'))
        if compressed_size < webp_compressed_size:
            # Copy file to the maximally_minimized
            shutil.move(compression_dir + '/' + file, smallest_dir + '/' + file)
        else:
            # Copy the webp file to the maximally_minimized
            curr_file = no_ext + '.webp'
            shutil.move(conversion_dir + '/' + curr_file, smallest_dir + '/' + curr_file)

    # Empty the working directories
    for f in listdir(compression_dir):
        remove(path.join(compression_dir, f))

    for f in listdir(conversion_dir):
        remove(path.join(conversion_dir, f))

print('Success...')


'''
Total Reduction Calculation 
'''
pre_compressed_sum = 0
post_compressed_sum = 0

files = next(walk(pre_process_dir), (None, None, []))[2]  # [] if no file
for file in files:
    pre_compressed_sum += path.getsize(path.join(pre_process_dir,file))

files = next(walk(smallest_dir), (None, None, []))[2]  # [] if no file
for file in files:
    post_compressed_sum += path.getsize(path.join(smallest_dir,file))

reduction_val = ((pre_compressed_sum - post_compressed_sum) / pre_compressed_sum) * 100
print('The images have been reduced by ', end='')
print(reduction_val, end='')
print('%')
