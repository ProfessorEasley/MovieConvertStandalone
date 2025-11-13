import platform
import sys
import os
from collections import namedtuple
import shutil
import re
import ffmpegUtil as fUt
import cv2

FileFormat = namedtuple('FileFormat', ['name', 'extension', 'is_movie'])
FILE_FORMATS = [FileFormat('PNG', 'png', False), FileFormat('JPEG', 'jpg', False), FileFormat('JPEG', 'jpeg', False), FileFormat('MP4', 'mp4', True), FileFormat('AVI', 'avi', True), FileFormat('MOV', 'mov', True)]
__output_log = ""
osName = ""
__sourceList = []
__outputFileFormat = None
__outputDir = ""
__outputFileName = "newFile"
__frameDigits = 0
__outputSize = []

class InputSource:
    def __init__(self, filePath):
        self.filePath = filePath
        self.fileName, _ = os.path.splitext(os.path.basename(filePath))
        self.ext = filePath.split(".")[-1]
        self.fileFormat = getFileFormat(self.ext)
    
def getOS():
    global osName
    osName = platform.system()
    isWindows = None
    if osName == "Windows":
        isWindows = True
    elif osName == "Darwin":
        isWindows = False
    return isWindows

def verifyFFMPEG(filepath =""):
    return fUt.check_ffmpeg(osName,filepath)

def getSourceDimensions(filePath):
    ext = filePath.split(".")[-1]
    w,h = None,None
    for ff in FILE_FORMATS:
        if ext == ff.extension and not ff.is_movie:
            w,h = __getImageDimensions(filePath)
        elif ext == ff.extension and ff.is_movie:
            w,h = __getVideoDimensions(filePath)

    return w,h

def __getImageDimensions(filePath):
    image = cv2.imread(filePath)
    width,height = None,None
    if image is not None:
        dimensions = image.shape

        # Extract height, width, and channels
        height = dimensions[0]
        width = dimensions[1]
        
    return width,height

def __getVideoDimensions(filePath):
    try:
        cap = cv2.VideoCapture(filePath)
        if not cap.isOpened():
            # print(f"Error: Could not open video file at {filePath}")
            return None, None

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
        return width, height
    except Exception as e:
        # print(f"Error processing video with OpenCV: {e}")
        return None, None


def getSourceList():
    return __sourceList

def verifySource(filePath):
    ext = filePath.split(".")[-1]
    pattern = r'(?<!\d)(0*1)$'
    fileFormat = getFileFormat(ext)
    fileName, _ = os.path.splitext(os.path.basename(filePath))
    if not fileFormat.is_movie:
        # number_string = filePath.split(".")[-2]
        match = re.search(pattern, fileName) # check if it's the first image in the sequence, i.e. ends with 01, 001, 0001 etc.
        if match:
            filePathwithPattern = os.path.join(os.path.dirname(filePath), f'{fileName[:match.start(1)]}%0{len(match.group(1))}d.{ext}')
            # print(filePathwithPattern)
            return True, filePathwithPattern

        else:
            return False , None
    elif fileFormat.is_movie:
            return True , filePath
        
    return False , None

def convertMovie(inputConversionData):
    global __output_log
    unpackData(inputConversionData)

    success, msg = fUt.convert(__sourceList, __outputDir, __outputFileName, __outputFileFormat, __frameDigits, __outputSize)
    __output_log += msg
    return __output_log
    

def unpackData(inputConversionData):
    global __output_log, __outputDir, __outputFileName, __outputFileFormat, __frameDigits, __outputSize, __outputFilePath
    __sourceList.clear()
    # input source list
    for inpSrc in inputConversionData["InputSources"]:
        __sourceList.append(InputSource(inpSrc))

    # Output options
    # 1. file format
    __outputFileFormat = getFileFormat(inputConversionData["OutputFormat"])
    __output_log += (f"Output File Format: {__outputFileFormat} \n")

    # 2. file Directory
    __outputDir = os.path.abspath(os.path.normpath(inputConversionData["OutputDir"]))
    if not __outputDir: __outputDir = os.path.dirname(os.path.abspath(__file__)) # set as current directory
    __output_log += (f"Output Dir: {__outputDir} \n")

    # 3. Full Path to Output file name 
    if inputConversionData["OutputFileName"]: 
        __outputFileName = inputConversionData["OutputFileName"]

    __output_log += (f"Output File Name: {__outputFileName} \n")

    # 4. frame digits
    if not __outputFileFormat.is_movie:
        __frameDigits = inputConversionData["OutputFrameDigits"]
    else:
        __frameDigits = 0
    __output_log += (f"Output Frame Digits: {__frameDigits} \n")
    
    # 5. file dimensions
    w = inputConversionData["OuputWidth"]
    h = inputConversionData["OuputHeight"]
    if inputConversionData["OuputWidth"] is None or inputConversionData["OuputHeight"] is None:
        wd,ht = getSourceDimensions(__sourceList[0].filePath)
        if inputConversionData["OuputWidth"] is None:
            w = wd
        if inputConversionData["OuputHeight"] is None:
            h = ht
        
    __outputSize = [w,h]

    __output_log += (f"Output Dimensions: {__outputSize} \n")

    # for src in __sourceList:
    #     print(src.filePath)
    #     print(src.fileFormat)
    #     if src.fileFormat.name == __outputFileFormat.name:
    #         __output_log += ("what do you want me to convert???\n")
    #     else:
    #         __output_log += ("converting now . . .\n")



def getFileFormat(ext):
    for ff in FILE_FORMATS:
        if ext.lower() == ff.extension:
            return ff

def addSource(filePath, ind, isOld):
    if len(__sourceList) -1 < ind:
        __sourceList.append(filePath)
    elif not isOld :
        __sourceList.insert(ind, filePath)
    else:
        __sourceList[ind] = filePath

    # print("on adding new source")
    print(__sourceList)

# def deleteFromSources(ind):
#     try:
#         __sourceList.pop(ind)
#         return True
#     except IndexError:
#         output_log.append("Empty source, nothing to delete.")
#         print(output_log)
#         return True
#     return False

def moveInSrc(oldInd, newInd, numSources):
    if numSources == len(__sourceList):
        item = __sourceList.pop(oldInd)
        __sourceList.insert(newInd, item)
    # print(__sourceList)

def checkIfFileExists(fileDir, fileName, fileFormat):
    filePath = os.path.join(fileDir, fileName + "." + fileFormat)
    if os.path.exists(filePath):
        return True
    return False

