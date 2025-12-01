# For DEV
## Env Set Up and Run Command for Terminal/Command Prompt
   > pip3 install pyqt6  
   > pip3 install opencv-python  
   > python3 movieConvert.py  

## Packaging For Windows:
   > pip3 install pyinstaller  
   > <"path-To-pyinstaller.exe"> --windowed --onefile --name “MovieConvert” --icon <"path-To-app_icon.ico”> movieConvert.py --add-data "ffmpeg;ffmpeg" --add-data "icons;icons"


## Packaging For MAC:
   > pip3 install pyinstaller  
   > pyinstaller --windowed --onefile --name MovieConvert --icon <path-To-app_icon.icns> movieConvert.py --add-binary ffmpeg:ffmpeg --add-data icons:icons
