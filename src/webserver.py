import urllib.request
import os,random,time,signal
from flask import Flask, flash, request, redirect, url_for,render_template
from werkzeug.utils import secure_filename
from flask import send_from_directory
from datetime import datetime
from PIL import Image
import json
from inky.auto import auto
import RPi.GPIO as GPIO
from PIL import ImageDraw, Image 
import requests
import generateInfo
import log
import time


# Gpio button pins from top to bottom

#5 == info
#6 == rotate clockwise
#16 == rotate counterclockwise
#24 == reboot

BUTTONS = [5, 6, 16, 24]
ORIENTATION = 0
ADJUST_AR = False

# Get the current path
PATH = os.path.dirname(os.path.dirname(__file__))
log.info(f"Webserver path: {PATH}")
UPLOAD_FOLDER = os.path.join(PATH, "img")
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
log.info(f"Allowed extensions: {ALLOWED_EXTENSIONS}")

# Check whether the specified path exists or not
pathExist = os.path.exists(os.path.join(PATH, "img"))

if(pathExist == False):
   os.makedirs(os.path.join(PATH, "img"))

#setup eink display and border
inky_display = auto(ask_user=True, verbose=True)
inky_display.set_border(inky_display.BLACK)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# Get the path of the directory above me
path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")

log.info(f"Looking for API Config in path: {path}")

# Load the file settings.json from that path
json_file = open(os.path.join(path, "config/api.json"))

# Load the json data from the file
settings_data = json.load(json_file)

# Get the frame value from settings_data
FRAME = settings_data.get("frame")
log.info(f"Frame #: {FRAME}")

# Get the base_url value
BASE_URL = settings_data.get("base_url")
log.info(f"API Base URL: {BASE_URL}")

INDEX_URL = f"{BASE_URL}/{FRAME}/index.json"
log.info(f"API Index URL: {INDEX_URL}")

#handles button presses
def handleButton(pin):
    #top button
    if(pin == 5):
        log.info("A Button Pressed - Update Image")
        download_file()
        # print("--A-- Pressed: Show PiInk info")
        # generateInfo.infoGen(inky_display.width,inky_display.height)
        # #update the eink display
        # updateEink("infoImage.png",0,"")
    elif(pin == 6):
        log.info("B Button Pressed - Rotate Clockwise")
        # print("--B-- Pressed: Rotate image clockwise")
        rotateImage(-90)
    elif(pin == 16):
        log.info("C Button Pressed - Rotate Image Counterclockwise")
        # print("--C-- Pressed: Rotate image counter clockwise")
        rotateImage(90)
    elif(pin == 24):
        log.info("D Button Pressed - Reboot Picture Frame")
        # print("--D-- Pressed: Reboot the Pi")
        os.system('sudo reboot')  

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def download_file():
    deleteImage()

    # Fetch the JSON file at index_url
    response = requests.get(INDEX_URL)
    index_json = response.json()

    # Get the url value from index_json
    image_url = index_json.get("url")
    log.info(f"Image URL: {image_url}")
    
    # Fetch the image at image_url
    image_response = requests.get(image_url)
    
    save_filename = os.path.join(app.config['UPLOAD_FOLDER'], "image.png")

    # Save the image to the img directory
    with open(save_filename, "wb") as image_file:
        image_file.write(image_response.content)

    print(f"Saved to {save_filename}")
    updateEink(save_filename, ORIENTATION, ADJUST_AR)


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    print("req ",request.files)    
    ADJUST_AR = False

    arSwitchCheck, horizontalOrientationRadioCheck, verticalOrientationRadioCheck = loadSettings()

    if horizontalOrientationRadioCheck == "checked":
        ORIENTATION = 0
    else:
        ORIENTATION = 1
    
    if arSwitchCheck == "checked":
        ADJUST_AR = True
    
    if request.method == 'POST':
        
        #print(request.form)
        #upload via link, add support in for api calls like cURL 'curl -X POST -F "file=@image.png" piink.local'
        if 'file' in request.files or (request.form and request.form.get("submit") == "Upload Image"):
            file = request.files['file']
            print(file)
            if file and allowed_file(file.filename):
                deleteImage()
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                filename = os.path.join(app.config['UPLOAD_FOLDER'],filename)

                #update the eink display
                updateEink(filename,ORIENTATION,ADJUST_AR)
                if(len(request.form) == 0):
                    return "File uploaded successfully", 200
            else:
                deleteImage()
                imageLink = request.form.getlist("text")[0]
                print(imageLink)
                try:
                    filename = imageLink.replace(":","").replace("/","")
                    filename = filename.split("?")[0]
                    print(filename)
                    #grab the url and download it to the folder
                    urllib.request.urlretrieve(imageLink, os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    updateEink(filename,ORIENTATION,ADJUST_AR)
                except:
                    #flash error message
                    flash("Error: Unsupported Media or Invalid Link!")
                    return render_template('main.html')
                    
        #other button funcs
        #reboot
        if request.form["submit"] == 'Reboot':
            print("reboot")
            os.system("sudo reboot")
        
        #shutdown
        if request.form["submit"] == 'Shutdown':
            print("shutdown")
            os.system("sudo shutdown")

        #rotate clockwise
        if request.form["submit"] == 'rotateImage':
            print("rotating image")
            rotateImage(-90)

        #ghosting clears
        if request.form["submit"] == 'clearGhost':
            print("ghosting clear call!")
            clearScreen()

        #save frame settings
        if request.form["submit"] == 'Save Settings':
            if(request.form["frame_orientation"] == "Horizontal Orientation"):
                horizontalOrientationRadioCheck = "checked"
                verticalOrientationRadioCheck = ""
            else:
                horizontalOrientationRadioCheck = ""
                verticalOrientationRadioCheck = "checked"
            try:
                if request.form["adjust_ar"] == "true":
                    arSwitchCheck = "checked"
            except:
                arSwitchCheck = ""
                pass
            saveSettings(horizontalOrientationRadioCheck,verticalOrientationRadioCheck,arSwitchCheck)
            return render_template('main.html',horizontalOrientationRadioCheck = horizontalOrientationRadioCheck,verticalOrientationRadioCheck=verticalOrientationRadioCheck,arSwitchCheck=arSwitchCheck)       
    return render_template('main.html',horizontalOrientationRadioCheck = horizontalOrientationRadioCheck,verticalOrientationRadioCheck=verticalOrientationRadioCheck,arSwitchCheck=arSwitchCheck)


def loadSettings():
    horizontalOrient = ""
    verticalOrient = ""
    try:
        jsonFile = open(os.path.join(PATH,"config/settings.json"))
    except:
        saveSettings("","checked",'aria-checked="false"')
        jsonFile = open(os.path.join(PATH,"config/settings.json"))
    settingsData = json.load(jsonFile)
    jsonFile.close()
    if settingsData.get("orientation") == "Horizontal":
        horizontalOrient = "checked"
        verticalOrient = ""
    else:
        verticalOrient = "checked"
        horizontalOrient = ""
    return settingsData.get("adjust_aspect_ratio"),horizontalOrient,verticalOrient


def saveSettings(orientationHorizontal, orientationVertical, adjustAR):
    if orientationHorizontal == "checked":
        orientationSetting = "Horizontal"
    else:
        orientationSetting = "Vertical"
    jsonStr = {
        "orientation":orientationSetting,
        "adjust_aspect_ratio":adjustAR,
    }
    with open(os.path.join(PATH,"config/settings.json"), "w") as f:
        json.dump(jsonStr, f)


def updateEink(filename, orientation, adjustAR):
    log.info(f"[Command] Update Image - Orientation={orientation}, AdjustAR={adjustAR}")
    with Image.open(os.path.join(PATH, "img/", filename)) as img:
        # do image transforms
        img = changeOrientation(img, orientation)
        img = adjustAspectRatio(img, adjustAR)

        # Display the image
        log.info("[Display] Set Image")
        inky_display.set_image(img)
        time.sleep(0.2)
        log.info("[Display] Show Image")
        inky_display.show()


#clear the screen to prevent ghosting
def clearScreen():
    print("[Command] Clear Screen")
    img = Image.new(mode="RGB", size=(inky_display.width, inky_display.height), color=(
        255,
        255,
        255
    ))
    inky_display.set_image(img)
    inky_display.show()
    updateEink(os.listdir(app.config['UPLOAD_FOLDER'])[0],ORIENTATION,ADJUST_AR)


def changeOrientation(img, orientation):
    # 0 = horizontal
    # 1 = portrait
    if orientation == 0:
        img = img.rotate(0)
    elif orientation == 1:
        img = img.rotate(90)
    return img


def adjustAspectRatio(img, adjustARBool):
    if adjustARBool:
        w = inky_display.width
        h = inky_display.height
        ratioWidth = w / img.width
        ratioHeight = h / img.height
        if ratioWidth < ratioHeight:
            # It must be fixed by width
            resizedWidth = w
            resizedHeight = round(ratioWidth * img.height)
        else:
            # Fixed by height
            resizedWidth = round(ratioHeight * img.width)
            resizedHeight = h
        imgResized = img.resize((resizedWidth, resizedHeight), Image.LANCZOS)
        background = Image.new('RGBA', (w, h), (0, 0, 0, 255))

        #offset image for background and paste the image
        offset = (round((w - resizedWidth) / 2), round((h - resizedHeight) / 2))
        background.paste(imgResized, offset)
        img = background
    else:
        img = img.resize(inky_display.resolution)
    return img


def deleteImage():
    img_directory = os.path.join(PATH, "img")
    log.info(f"Deleting Images in path: {img_directory}")
    for filename in os.listdir(img_directory):
        fp = os.path.join(img_directory, filename)
        if os.path.isfile(fp):
            os.remove(fp)
            

def rotateImage(deg):   
    with Image.open(os.path.join(PATH, "img/" ,os.listdir(app.config['UPLOAD_FOLDER'])[0])) as img:
        #rotate image by degrees and update
        img = img.rotate(deg, Image.NEAREST,expand=1)
        img = img.save(os.path.join(PATH, "img/",os.listdir(app.config['UPLOAD_FOLDER'])[0]))
        updateEink(os.listdir(app.config['UPLOAD_FOLDER'])[0],ORIENTATION,ADJUST_AR)


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],filename)


# ALWAYS CHECK OUR NEW IMAGE
# ----------------------------------------------------------------------------

log.info("Upon webserver startup, downloading image.")
download_file()

# INITIALIZE THE BUTTONS
# ----------------------------------------------------------------------------

if __name__ == '__main__':
    try:
        log.info("Upon webserver startup, initialize buttons.")
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(BUTTONS, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        time.sleep(0.2)

        for pin in BUTTONS:
            print(f"Trying to add event detect for pin {pin}")
            GPIO.add_event_detect(pin, GPIO.FALLING, handleButton, bouncetime=250)
            time.sleep(0.1)

        app.secret_key = str(random.randint(100000, 999999))

        app.run(host="0.0.0.0", port=80)
    except Exception as e:
        log.exception(e)
    finally:
        GPIO.cleanup()
        log.info("GPIO cleanup complete.")