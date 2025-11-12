import platform
import sys
import os
import shutil
import subprocess
import re
import tempfile

ffmpegCommand = []
ffmpegPath = "ffmpeg"
kwargs = {}
os_Name = ""
def check_ffmpeg(osName,filePath= "" ):
    """
    Checks if the ffmpeg executable exists within the Python application's folder.
    Returns the full path to ffmpeg if found, otherwise returns None.
    """
    global ffmpegPath, os_Name
    os_Name = osName
    # Define potential ffmpeg executable names for different OS
    ffmpeg_names = ["ffmpeg", "ffmpeg.exe"]
    print(osName)

    if filePath:
        filePath1 = filePath.replace("\\","/")
        fileName = filePath1.split("/")[-1]
        if fileName in ffmpeg_names and os.path.exists(filePath):
            if os_Name == "Windows": ffmpegPath = filePath
            return [filePath, True]
        else:
            return ["Incorrect File. Please select again.", False]

    
    if getattr(sys, 'frozen', False):
        # if running application.exe 
        base_path = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(sys.executable)
    else:
        # Get the directory of the current script
        base_path = os.path.dirname(os.path.abspath(__file__))

    ffmpegDir_path = None
    if osName == "Darwin":
        ffmpegDir_path = base_path
            
    elif osName == "Windows":
        listOfDir = os.listdir(base_path)
        for dir in listOfDir:
            dir_path = os.path.join(base_path ,dir )
            if os.path.isdir(dir_path) and "ffmpeg" in dir.lower():
                bin_path =  os.path.join(dir_path, "bin")
                print(bin_path)
                if os.path.isdir(bin_path): 
                    ffmpegDir_path = bin_path
                    print(ffmpegDir_path)
                    break
                
    
    if ffmpegDir_path:
        for name in ffmpeg_names:
            ffmpeg_path = os.path.join(ffmpegDir_path, name)
            print(ffmpeg_path)
            if os.path.exists(ffmpeg_path) and os.path.isfile(ffmpeg_path) and os.access(ffmpeg_path, os.X_OK):
               print("Its a file") 
               if osName == "Windows": ffmpegPath = ffmpeg_path
               return [ffmpeg_path, True]
		
            else:
                ffmpeg_path = "Couldn't find ffmpeg.exe file. Please browse and select manually." 
                
    return [ffmpeg_path, False]

def setSubprocessOptions():
    kwargs = {
        "stdout" : subprocess.PIPE,
        "stderr" : subprocess.PIPE,
        "text" : True,
        "shell" : False
    }

    if os_Name == "Windows":
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW


def convert(sourceList, outputDir, outputFileName, outputFileFormat, frameDigits, outputSize):
    setSubprocessOptions()
    # ffmpegCommand = ["ffmpeg", "-nostdin", "-y"]
    numSources = len(sourceList)
    outputFilePath = os.path.join(outputDir, f"{outputFileName}.{outputFileFormat.extension}")
    if outputFileFormat.is_movie:
        success, msg = convertToVideo(numSources, sourceList, outputFileFormat, outputFilePath, outputSize)

    elif not outputFileFormat.is_movie:
        success, msg = convertToImages(numSources, sourceList, outputFileFormat, outputDir, outputFileName, outputSize, frameDigits)

    return success, msg
        


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
            print("========================================================================================")
            print(video_paths)
            # input("\n⏸️ Paused. Check temp files, then press Enter to continue...")
            if len(video_paths) > 1:
                success, msg = concatVideos(video_paths, outputFilePath, outputFileFormat, outputSize)
            
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

    return success, msg

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

        
        success, msg = convertToImgSeq(ffmpegCommand, inputFilePath, outputSize, outputFileFormat, outputFilePath)

    return success, msg

def convertImgSeqtoMov(outputFilePath, ffmpegCommand, inputFile, inputFilePattern, outputFileFormat, outputSize):
    inputFilePathwithPattern = os.path.join(os.path.dirname(inputFile.filePath), inputFilePattern)

    print("========================================================================================")
    print(inputFilePathwithPattern)
    ffmpegCommand += ["-framerate", "24", "-i", inputFilePathwithPattern, "-vf", f"scale={outputSize[0]}:{outputSize[1]}", "-vsync", "vfr"]

    ffmpegCommand = getFFmpegVidCodec(ffmpegCommand, outputFileFormat)
        
    ffmpegCommand += [outputFilePath]

    print("========================================================================================")
    print("Converting img seq to video using: ",ffmpegCommand)

    try:
        subprocess.run(ffmpegCommand, **kwargs, check=True)

        return outputFilePath

    except subprocess.CalledProcessError as e:
        return None

def convertToImgSeq(ffmpegCommand, inputFilePath, outputSize, outputFileFormat, outputFilePath):
    ffmpegCommand += ["-i" , inputFilePath, "-vf", f"scale={outputSize[0]}:{outputSize[1]}"]
    if outputFileFormat.extension in ["jpg", "jpeg"]:
        ffmpegCommand+= ["-q:v", "2"]
    
    ffmpegCommand += [outputFilePath]

    try:
        print("========================================================================================")
        print("Converting video to Img seq using: ",ffmpegCommand)
        result = subprocess.run(ffmpegCommand, **kwargs, check=True)
        print("========================================================================================")
        print(outputFilePath)
        return True, f"Success: images created at : {outputFilePath}"
    except subprocess.CalledProcessError as e:
        return False, f"Failed: Couldn't convert to images because of the following error: {e}"



def convertVideoFormat(outputFilePath, ffmpegCommand, inputFile, outputFileFormat, outputSize):

    print("========================================================================================")
    print(inputFile.filePath)
    ffmpegCommand += ["-i", inputFile.filePath, "-vf", f"scale={outputSize[0]}:{outputSize[1]}"]
    ffmpegCommand = getFFmpegVidCodec(ffmpegCommand, outputFileFormat)

    ffmpegCommand += [outputFilePath]
    try:
        print("========================================================================================")
        print("Converting video format using: ",ffmpegCommand)
        subprocess.run(ffmpegCommand, **kwargs, check=True)
        print("========================================================================================")
        print(outputFilePath)
        return outputFilePath
    except subprocess.CalledProcessError as e:
        print(e)
        return None



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
    try:
        print("Concatenating videos with command:", " ".join(cmd))
        subprocess.run(cmd, **kwargs, check=True)
        os.remove(list_file_path)
        return True, f"Success: Video Created at {outputFilePath}"
    except subprocess.CalledProcessError as e:
        return False, f"FFMPEG ERROR: couldn't convert to video with error {e}"
    
def getFilePattern(fileName, ext, padding = None):

    match = re.search(r'(?<!\d)(0*1)$', fileName) # find a pattern of numbers like 01,001,0001 etc. in the file name
    if padding is None and match:
        number_part = match.group(1)
        print(number_part)
        filePattern = f'{fileName[:match.start(1)]}%0{len(match.group(1))}d.{ext}'
        print(filePattern)

    else:
        filePattern = f'{fileName}_%0{padding}d.{ext}'
        print(filePattern)

    return filePattern


def getFFmpegVidCodec(ffmpegCommand, fileFormat):
    if fileFormat.extension == "mp4":
        # ffmpegCommand += ['-c:v','libx264','-c:a', 'aac', '-movflags', '+faststart']
        ffmpegCommand += ['-c:v','libx264','-an', '-movflags', '+faststart']
    elif fileFormat.extension == "avi":
        ffmpegCommand += ['-c:v', 'rawvideo', '-pix_fmt', 'yuv420p']
    elif fileFormat.extension == "mov":
        ffmpegCommand += ['-c:v', 'mjpeg', '-q:v', '3']
    else:
        print("unsupported file pattern")

    return ffmpegCommand
    


