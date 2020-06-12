import os, os.path
import subprocess
import wave
from datetime import datetime, timedelta
from cdputils import cdpwavefile
import socket

FFMPEG_FILE_LIST_PATH=os.path.join("C:\\Presenter Storage\\RNH Automation","NewsFiles.txt")
NEWS_FILE_NAME_1_MIN="C:\\Users\\hcr-myriad-server\\Dropbox\\RNH-bulletins\\news.mp3"
NEWS_FILE_NAME_2_MIN="C:\\Users\\hcr-myriad-server\\Dropbox\\RNH-bulletins\\twominnews.mp3"
NEWS_WAV_FILE_PATH="C:\\Presenter Storage\\RNH Automation\\RNHNews.wav"
NEWS_BUMPER_FILE_PATH="C:\\Presenter Storage\\RNH Automation\\NewsOut.wav"
NEWS_OUTPUT_NOMETA_FILE_PATH="C:\\Presenter Storage\\RNH Automation\\NewsNoMeta.wav"
NEWS_OUTPUT_META_FILE_PATH="C:\\Presenter Storage\\RNH Automation\\NewsMeta.wav"

#epoch = datetime.datetime.utcfromtimestamp(0)

NEWS_MP3_FILE_PATH = NEWS_FILE_NAME_2_MIN if os.path.exists(NEWS_FILE_NAME_2_MIN) and (datetime.now()- datetime.fromtimestamp(os.path.getmtime(NEWS_FILE_NAME_2_MIN))).total_seconds() < 3600 else NEWS_FILE_NAME_1_MIN

# First, convert the MP3 news to WAV

subprocess.Popen(["ffmpeg",
			"-i", NEWS_MP3_FILE_PATH,
			"-c:a", "pcm_s16le",
                        "-ar", "44100",
                        "-y",
			NEWS_WAV_FILE_PATH
			], shell=False).wait()

# Now concat the files
with open(FFMPEG_FILE_LIST_PATH, 'w',) as f:
    f.write("file '{0}'\r\n".format(NEWS_WAV_FILE_PATH))
    f.write("file '{0}'\r\n".format(NEWS_BUMPER_FILE_PATH))

subprocess.Popen(["ffmpeg",
                  "-f", "concat",
                  "-safe", "0",
                  "-i", FFMPEG_FILE_LIST_PATH,
                  "-c", "copy",
                  #"-q:a", "2",
                  "-y",
                  NEWS_OUTPUT_NOMETA_FILE_PATH
                  ], shell=False).wait()

os.remove(FFMPEG_FILE_LIST_PATH)
os.remove(NEWS_WAV_FILE_PATH)

# Now calculate the offset for the extro/SEG1 marker (2 secs from end)
sampleRate=0
segueSecsFromEnd=2
sampleCount=0

wavFile = wave.open(NEWS_OUTPUT_NOMETA_FILE_PATH, mode='rb')
sampleRate = wavFile.getframerate()
sampleCount= wavFile.getnframes()
wavFile.close()

segueSamplesFromEnd = sampleRate*segueSecsFromEnd
segueSamplesFromStart = sampleCount-segueSamplesFromEnd

xml = """<?xml version=\"1.0\" ?>
<cart>
    <version>0101</version>
    <title>RNH News {hourTop}</title>
    <artist>Radio NewsHub</artist>
    <cutnum></cutnum>
    <clientid></clientid>
    <category>NEWS</category>
    <classification></classification>
    <outcue></outcue>
    <outcue></outcue>
    <startdate>{inDate}</startdate>
    <starttime>{inTime}</starttime>
    <enddate>{outDate}</enddate>
    <endtime>{outTime}</endtime>
    <appid>HCRNewsConverter</appid>
    <appver>1.0</appver>
    <userdef></userdef>
    <zerodbref>0</zerodbref>
    <posttimers><timer type="SEG1">{segTime}</timer></posttimers>
    <url></url>
</cart>""".format(hourTop=(datetime.now()+timedelta(hours=1)).strftime("%H:00"),
                  inDate=datetime.now().strftime("%Y/%m/%d"),
                  inTime=datetime.now().strftime("%H:%M:%S"),
                  outDate=(datetime.now()+timedelta(hours=1)).strftime("%Y/%m/%d"),
                  outTime=(datetime.now()+timedelta(hours=1)).strftime("%H:%M:%S"),
                  segTime=segueSamplesFromStart)

cdpFile = cdpwavefile.CDPFile()
cdpFile.ReadWaveFile(NEWS_OUTPUT_NOMETA_FILE_PATH)
cdpFile.cart.ImportXMLValues(xml)
cdpFile.WritePCMWaveFile(NEWS_OUTPUT_META_FILE_PATH)

os.remove(NEWS_OUTPUT_NOMETA_FILE_PATH)

# And finally, import it to Myriad
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("192.168.0.4", 6950))
s.send("""AUDIOWALL IMPORTFILE "{audioFilePath}",15000,Delete\n""".format(audioFilePath=NEWS_OUTPUT_META_FILE_PATH))
