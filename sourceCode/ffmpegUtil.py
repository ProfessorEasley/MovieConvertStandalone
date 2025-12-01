import platform
import sys
import os
import shutil
import subprocess
import re
import tempfile
import traceback

ffmpegCommand = []
ffmpegPath = "ffmpeg"
kwargs = {}
os_Name = ""

log_dir = os.path.expanduser("~/MovieConvertLogs")
os.makedirs(log_dir, exist_ok=True)  # create directory if it doesn't exist

ffmpeg_log_path = os.path.join(log_dir, "ffmpeg_log.txt")
error_log_path = os.path.join(log_dir, "error_log.txt")

# Set working directory to the folder containing the executable or script
if getattr(sys, 'frozen', False):
    # running from PyInstaller bundle
    os.chdir(os.path.dirname(sys.executable))
else:
    # running in development
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

def basePath():
    import sys, os
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return base_path
    # return os.path.join(base_path, relative_path)

def check_ffmpeg(osName,filePath= "" ):
    """
    Checks if the ffmpeg executable exists within the Python application's folder.
    Returns the full path to ffmpeg if found, otherwise returns None.
    """
    global ffmpegPath, os_Name
    os_Name = osName
    # Define potential ffmpeg executable names for different OS
    ffmpeg_names = ["ffmpeg", "ffmpeg.exe"]

    if filePath:
        filePath1 = filePath.replace("\\","/")
        fileName = filePath1.split("/")[-1]
        if fileName in ffmpeg_names and os.path.exists(filePath):
            ffmpegPath = filePath
            return [filePath, True]
        else:
            return ["Incorrect File. Please select again.", False]

    base_path = basePath()

    ffmpegDirPath = os.path.join(base_path, "ffmpeg")
    if os_Name == "Windows":
        ffmpegDirPath = os.path.join(ffmpegDirPath, "bin")         
    
    if os.path.isdir(ffmpegDirPath):
        for name in ffmpeg_names:
            ffmpeg_path = os.path.join(ffmpegDirPath, name)
            # print(ffmpeg_path)
            if os.path.exists(ffmpeg_path) and os.path.isfile(ffmpeg_path) and os.access(ffmpeg_path, os.X_OK):
               ffmpegPath = ffmpeg_path
               return [ffmpeg_path, True]
		
            else:
                ffmpeg_path = "Couldn't find ffmpeg.exe file. Please browse and select manually." 
                
    return ["Couldn't find ffmpeg.exe file. Please browse and select manually." , False]


def run_ffmpeg(cmd):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        if result.returncode != 0:
            # Write stderr to a log file for debugging
            with open(ffmpeg_log_path, "w") as f:
                f.write(result.stderr or "ffmpeg failed with no stderr output")
            # print("FFmpeg failed! Check ffmpeg_log.txt")
        else:
            # print("FFmpeg succeeded.")
            return True
    except Exception as e:
        # print("FFmpeg Error.", e)
        with open(error_log_path, "w") as f:
            f.write(traceback.format_exc())

    return False


def convert(sourceList, outputDir, outputFileName, outputFileFormat, frameDigits, outputSize):
    # setSubprocessOptions()
    # ffmpegCommand = ["ffmpeg", "-nostdin", "-y"]
    numSources = len(sourceList)
    outputFilePath = os.path.join(outputDir, f"{outputFileName}.{outputFileFormat.extension}")
    if outputFileFormat.is_movie:
        success, outputFilePath, msg = convertToVideo(numSources, sourceList, outputFileFormat, outputFilePath, outputSize)

    elif not outputFileFormat.is_movie:
        success,outputFilePath, msg = convertToImages(numSources, sourceList, outputFileFormat, outputDir, outputFileName, outputSize, frameDigits)

    return success,outputFilePath, msg


def convertToVideo(numSources, sourceList, outputFileFormat, outputFilePath, outputSize):
    success, msg = False, ""
    if numSources >1:
        with tempfile.TemporaryDirectory() as temp_dir:
            video_paths = []
            for idx,inputFile in enumerate(sourceList):
                ffmpegCommand = [ffmpegPath, "-nostdin", "-y"]
                tempOutputFilePath = os.path.join(temp_dir, f"temp_seq_{idx}.{outputFileFormat.extension}")
                if not inputFile.fileFormat.is_movie:
                    inputFilePattern = getFilePattern(inputFile.fileName, inputFile.fileFormat.extension)
                    vid_path = convertImgSeqtoMov(tempOutputFilePath, ffmpegCommand, inputFile, inputFilePattern, outputFileFormat, outputSize)
                elif inputFile.fileFormat.is_movie:
                    vid_path = convertVideoFormat(tempOutputFilePath, ffmpegCommand, inputFile, outputFileFormat, outputSize)
                if vid_path is not None:
                    video_paths.append(vid_path)
            # print("========================================================================================")
            # print(video_paths)
            # input("\n⏸️ Paused. Check temp files, then press Enter to continue...")
            if len(video_paths) > 1:
                success, outputFilePath, msg = concatVideos(video_paths, outputFilePath, outputFileFormat, outputSize)
            
    elif numSources ==1:
        ffmpegCommand = [ffmpegPath, "-nostdin", "-y"]
        if not sourceList[0].fileFormat.is_movie:
            inputFilePattern = getFilePattern(sourceList[0].fileName, sourceList[0].fileFormat.extension)
            vid_path = convertImgSeqtoMov(outputFilePath, ffmpegCommand, sourceList[0], inputFilePattern, outputFileFormat, outputSize)
        elif sourceList[0].fileFormat.is_movie:
            vid_path = convertVideoFormat(outputFilePath, ffmpegCommand, sourceList[0], outputFileFormat, outputSize)
        if vid_path:
            success = True
            msg = f"Sucess: Video Created at: {vid_path}"
            outputFilePath = vid_path

    return success, outputFilePath, msg


def convertToImages(numSources, sourceList, outputFileFormat, outputDir, outputFileName, outputSize, frameDigits):
    success, msg = False, ""
    newdir = outputDir

    for idx,inputFile in enumerate(sourceList):
        ffmpegCommand = [ffmpegPath, "-nostdin", "-y"]

        if inputFile.fileFormat.is_movie:
            inputFilePath = inputFile.filePath
            inputFileName = inputFile.fileName
        elif not inputFile.fileFormat.is_movie:
            if inputFile.fileFormat.extension != outputFileFormat.extension:
                inputFilePattern = getFilePattern(inputFile.fileName, inputFile.fileFormat.extension)
                inputFilePath = os.path.join(os.path.dirname(inputFile.filePath), inputFilePattern)
                inputFileName = os.path.basename(os.path.dirname(inputFile.filePath))
            else:
                success = True
                msg = f"Skipping {inputFile.filePath}. Nothing to convert."
                return success, msg

        if numSources >1:
            newdir = os.path.join(outputDir, inputFileName)
            os.makedirs(newdir, exist_ok=True)
        
        outputFilePattern = getFilePattern(outputFileName, outputFileFormat.extension, frameDigits)
        outputFilePath = os.path.join(newdir, outputFilePattern)
        
        success, outputFilePath, msg = convertToImgSeq(ffmpegCommand, inputFilePath, outputSize, outputFileFormat, outputFilePath)

    return success, outputFilePath, msg


def convertImgSeqtoMov(outputFilePath, ffmpegCommand, inputFile, inputFilePattern, outputFileFormat, outputSize):
    inputFilePathwithPattern = os.path.join(os.path.dirname(inputFile.filePath), inputFilePattern)

    # print("========================================================================================")
    # print(inputFilePathwithPattern)
    ffmpegCommand += ["-framerate", "24", "-i", inputFilePathwithPattern, "-vf", f"scale={outputSize[0]}:{outputSize[1]}", "-vsync", "vfr"]

    ffmpegCommand = getFFmpegVidCodec(ffmpegCommand, outputFileFormat)
        
    ffmpegCommand += [outputFilePath]

    # print("========================================================================================")
    # print("Converting img seq to video using: ",ffmpegCommand)

    if run_ffmpeg(ffmpegCommand):
        return outputFilePath
    
    return None
    # try:
    #     subprocess.run(ffmpegCommand, **kwargs, check=True)

    #     return outputFilePath

    # except subprocess.CalledProcessError as e:
    #     return None


def convertToImgSeq(ffmpegCommand, inputFilePath, outputSize, outputFileFormat, outputFilePath):
    ffmpegCommand += ["-i" , inputFilePath, "-vf", f"scale={outputSize[0]}:{outputSize[1]}"]
    if outputFileFormat.extension in ["jpg", "jpeg"]:
        ffmpegCommand+= ["-q:v", "2"]
    
    ffmpegCommand += [outputFilePath]

    if run_ffmpeg(ffmpegCommand):
        return True, outputFilePath, f"Success: images created at : {outputFilePath}"
    
    return False, "", f"Failed: Couldn't convert to images because of the following error."
    # try:
    #     print("========================================================================================")
    #     print("Converting video to Img seq using: ",ffmpegCommand)
    #     result = subprocess.run(ffmpegCommand, **kwargs, check=True)
    #     print("========================================================================================")
    #     print(outputFilePath)
    #     return True, f"Success: images created at : {outputFilePath}"
    # except subprocess.CalledProcessError as e:
    #     return False, f"Failed: Couldn't convert to images because of the following error: {e}"



def convertVideoFormat(outputFilePath, ffmpegCommand, inputFile, outputFileFormat, outputSize):

    # print("========================================================================================")
    # print(inputFile.filePath)
    ffmpegCommand += ["-i", inputFile.filePath, "-vf", f"scale={outputSize[0]}:{outputSize[1]}"]
    ffmpegCommand = getFFmpegVidCodec(ffmpegCommand, outputFileFormat)

    ffmpegCommand += [outputFilePath]

    if run_ffmpeg(ffmpegCommand):
        return outputFilePath
    
    return None
    # try:
    #     print("========================================================================================")
    #     print("Converting video format using: ",ffmpegCommand)
    #     subprocess.run(ffmpegCommand, **kwargs, check=True)
    #     print("========================================================================================")
    #     print(outputFilePath)
    #     return outputFilePath
    # except subprocess.CalledProcessError as e:
    #     print(e)
    #     return None



def concatVideos(videoPaths, outputFilePath, outputFileFormat, outputSize):
    cmd = [ffmpegPath, "-nostdin", "-y"]
    filterGraph = ""
    concatFilter = ""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as list_file:
        for idx,path in enumerate(videoPaths):
            cmd += ["-i", path]
            filterGraph += f"[{idx}:v]scale={outputSize[0]}:{outputSize[1]},setsar=1:1[vs{idx}];"
            concatFilter += f"[vs{idx}]"
        list_file_path = list_file.name

    concatFilter += f"concat=n={len(videoPaths)}:v=1:a=0[v]"
    filterGraph += concatFilter
    cmd += [ "-filter_complex", filterGraph,
        "-map", "[v]",
        "-r", "24" # output framerate needs to be defined for "Frame rate very high for a muxer not efficiently supporting it."
    ]

    cmd = getFFmpegVidCodec(cmd, outputFileFormat)
    cmd += [outputFilePath]

    if run_ffmpeg(cmd):
        os.remove(list_file_path)
        return True, outputFilePath, f"Success: Video created at : {outputFilePath}"
    
    return False, "", f"FFMPEG ERROR: couldn't concatenate videos."

    # try:
    #     print("Concatenating videos with command:", " ".join(cmd))
    #     subprocess.run(cmd, **kwargs, check=True)
    #     os.remove(list_file_path)
    #     return True, f"Success: Video Created at {outputFilePath}"
    # except subprocess.CalledProcessError as e:
    #     return False, f"FFMPEG ERROR: couldn't convert to video with error {e}"
    
def getFilePattern(fileName, ext, padding = None):

    match = re.search(r'(?<!\d)(0*1)$', fileName) # find a pattern of numbers like 01,001,0001 etc. in the file name
    if padding is None and match:
        number_part = match.group(1)
        # print(number_part)
        filePattern = f'{fileName[:match.start(1)]}%0{len(match.group(1))}d.{ext}'
        # print(filePattern)

    else:
        filePattern = f'{fileName}_%0{padding}d.{ext}'
        # print(filePattern)

    return filePattern


def getFFmpegVidCodec(ffmpegCommand, fileFormat):
    if fileFormat.extension == "mp4":
        # ffmpegCommand += ['-c:v','libx264','-c:a', 'aac', '-movflags', '+faststart']
        ffmpegCommand += ['-c:v','libx264','-an', '-movflags', '+faststart']
    elif fileFormat.extension == "avi":
        if fileFormat.forMaya:
            ffmpegCommand += ['-c:v', 'rawvideo', '-pix_fmt', 'yuv420p'] # grainy if not for maya
        else:
            ffmpegCommand += ['-c:v', 'rawvideo', '-pix_fmt', 'bgr24'] # windows media player compatible, not grainy
    elif fileFormat.extension == "mov":
        if fileFormat.forMaya:
            ffmpegCommand += ['-c:v', 'mjpeg', '-q:v', '3']
        else:
            ffmpegCommand += ['-c:v', 'prores_ks', '-profile:v', '3']
    # else:
    #     ("unsupported file pattern")

    return ffmpegCommand
    


