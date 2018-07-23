import os
import imghdr
import shutil
import struct
import argparse

silent_mode = False

def debug_print(output, silent=False):
    if not silent_mode:
        print(output)
    pass
    #end debug_print()


def get_image_size(fname):
    '''Determine the image type of fhandle and return its size.
    from draco'''
    with open(fname, 'rb') as fhandle:
        head = fhandle.read(24)
        if len(head) != 24:
            return
        if imghdr.what(fname) == 'png':
            check = struct.unpack('>i', head[4:8])[0]
            if check != 0x0d0a1a0a:
                return
            width, height = struct.unpack('>ii', head[16:24])
        elif imghdr.what(fname) == 'gif':
            width, height = struct.unpack('<HH', head[6:10])
        elif imghdr.what(fname) == 'jpeg':
            try:
                fhandle.seek(0) # Read 0xff next
                size = 2
                ftype = 0
                while not 0xc0 <= ftype <= 0xcf:
                    fhandle.seek(size, 1)
                    byte = fhandle.read(1)
                    while ord(byte) == 0xff:
                        byte = fhandle.read(1)
                    ftype = ord(byte)
                    size = struct.unpack('>H', fhandle.read(2))[0] - 2
                # We are at a SOFn block
                fhandle.seek(1, 1)  # Skip `precision' byte.
                height, width = struct.unpack('>HH', fhandle.read(4))
            except Exception: #IGNORE:W0703
                return
        else:
            return
        return width, height
    #end get_image_size()


def get_spotlight_path():
    # Windows Spotlight Path like this:
    # C:\Users\Yourname\AppData\Local\Packages\Microsoft.Windows.ContentDeliveryManager_cw5n1h2txyewy\LocalState\Assets
    # "cw5n1h2txyewy" could be random, "Microsoft.Windows.ContentDeliveryManager" is fixed
    SPOTLIGHT_PREFIX = r"Microsoft.Windows.ContentDeliveryManager"

    # 1.Get Local Path - C:\Users\Yourname\AppData\Local
    local_path = os.getenv("LOCALAPPDATA")
    if local_path == None:
        debug_print("Can not find User Local Path!")
        return None
    debug_print("local_path = " + local_path)

    # 2.Enum ContendDeliveryManager path
    package_path = local_path + "\\Packages\\"
    spot_path = None
    debug_print("package_path = " + package_path)
    dirlist = os.listdir(package_path)
    for dirname in dirlist:
        if dirname.find(SPOTLIGHT_PREFIX) != -1:
            # test whether this is spotlight path
            debug_print(dirname)
            spot_path = package_path + dirname + "\\LocalState\\Assets\\"
            if os.path.lexists(spot_path):
                # test whether exists files
                debug_print("Spotlight Path exists!")
                filelist = os.listdir(spot_path)
                if len(filelist) > 0:
                    debug_print(spot_path)
                    return spot_path

    return None
    #end get_spotlight_path()


def pickup_vertical(dest_dir, wallpaper_list):
    # 1st, create a seperate dir for vertical pics
    vert_dir = dest_dir + "\\vertical\\"
    if not os.path.lexists(vert_dir):
        os.mkdir(vert_dir)

    #enum copyied wallpapers in dest directory
    pics_count = 0
    try:
        #filelist = os.listdir(dest_dir)
        #for filename in filelist:
        for filename in wallpaper_list:
            # skip directory
            path_name = dest_dir + "\\" + filename
            if os.path.isdir(path_name):
                continue

            # get image size        
            img_size = get_image_size(path_name)
            debug_print(filename + " : " + str(img_size))
            pics_count += 1

            # if X and Y size below 300, is not a wallpaper
            if img_size[0] <= 300 and img_size[1] <= 300:
                debug_print("  is not a wallpaper, removed")
                os.remove(path_name)
                pics_count -= 1
            elif img_size[0] < img_size[1]:
                debug_print("  vertical wallpaper found, move it")
                shutil.move(path_name, vert_dir + "\\" + filename)
            else:
                debug_print("  normal horizental wallpaper")

        debug_print("Total " + str(pics_count) + " wallpapers copied.")
        return pics_count
    except Exception as e:
        print(Exception + ":" + str(e))

    #end pickup_vertical()


def copy_spotlight_pics(dest_dir):
    # create directory if not exists
    try:
        if not os.path.lexists(dest_dir):
            os.mkdir(dest_dir)
    except Exception as e:
        print("Exception: " + str(e))
        return 0

    debug_print("PASS dest_dir check")

    # get spotlight path
    spotlight_path = get_spotlight_path()
    if spotlight_path == None:
        print("Can't find Spotlight path!")
        return 0

    # get file list
    filelist = os.listdir(spotlight_path)
    if len(filelist) <= 0:
        debug_print("Can't find files in Spotlight path!")
        return 0

    # record wallpapers list
    wallpaper_list = []
    # enum files in given path
    for filename in filelist:
        src_path = spotlight_path + filename
        file_type = imghdr.what(src_path)
        # only jpeg type is wallpaper
        if file_type == "jpeg":
        # copy file to new dest dir and correct suffix
            try:
                debug_print("find wallpaper: " + filename)
                filename = filename + "." + file_type
                wallpaper_list.append(filename)

                dest_path = dest_dir + "\\" + filename
                shutil.copyfile(src_path, dest_path)
                debug_print("dest path: " + dest_path)
            except Exception as e:
                print(Exception, ":", e)

    return pickup_vertical(dest_dir, wallpaper_list)
    #end copy_spotlight_pics()


def format_dest_dir(dest_dir, default_dir):
    """Validate and format user input directory as destination directory"""
    #process no input
    formated_dir = dest_dir.strip()
    if formated_dir == "":
        formated_dir = default_dir

    #normalize path
    formated_dir = os.path.normpath(formated_dir)
    if formated_dir == ".":
        formated_dir = os.getcwd()

    debug_print("Destination Dir = " + formated_dir)
    return formated_dir
    #end format_dest_dir()

def process_cmdline_args():
    parser = argparse.ArgumentParser(description="Get Win10 Spotlight wallpapers")
    parser.add_argument("-d", "--dest", help="destination directory")
    parser.add_argument("-s", "--silent", action="store_true", help="silent mode")
    args = parser.parse_args()
    return args.dest, args.silent
    #end process_cmdline_args()

#-----------------
DEFAULT_DEST_DIR = "C:\\Spotlight"
dest_dir, silent_mode = process_cmdline_args()
debug_print("args.dest_dir = " + str(dest_dir))
debug_print("args.silent_mode: " + str(silent_mode))

if dest_dir == None:
    dest_dir = input("Input destination path, default use " + DEFAULT_DEST_DIR + "\n")
dest_dir = format_dest_dir(dest_dir, DEFAULT_DEST_DIR)

pics_count = copy_spotlight_pics(dest_dir)
print("Total " + str(pics_count) + " wallpapers copied to  " + dest_dir)
