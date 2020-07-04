import os, os.path
import subprocess
import wave
from datetime import datetime, timedelta
from cdputils import cdpwavefile
import socket

ADVERT_FILE_NAME_1="C:\\Users\\hcr-myriad-server\\Dropbox\\RNH-bulletins\\Advert1.mp3"
ADVERT_FILE_NAME_2="C:\\Users\\hcr-myriad-server\\Dropbox\\RNH-bulletins\\Advert2.mp3"
ADVERT_WAV_FILE_PATH="C:\\Presenter Storage\\RNH Automation\\BOHAdvert.wav"
ADVERT_OUTPUT_META_FILE_PATH="C:\\Presenter Storage\\RNH Automation\\BOHAdvertMeta.wav"

#epoch = datetime.datetime.utcfromtimestamp(0)

ADVERT_MP3_FILE_PATH = ADVERT_FILE_NAME_2 if os.path.exists(ADVERT_FILE_NAME_2) and (datetime.now()- datetime.fromtimestamp(os.path.getmtime(ADVERT_FILE_NAME_2))).total_seconds() < 3600 else ADVERT_FILE_NAME_1

# First, convert the MP3 news to WAV

subprocess.Popen(["ffmpeg",
			"-i", ADVERT_MP3_FILE_PATH,
			"-c:a", "pcm_s16le",
                        "-ar", "44100",
                        "-y",
			ADVERT_WAV_FILE_PATH
			], shell=False).wait()
# Now calculate the offset for the extro/SEG1 marker (1 sec from end)
sampleRate=0
segueSecsFromEnd=0.25
introSecsFromStart=0.25
sampleCount=0

wavFile = wave.open(ADVERT_WAV_FILE_PATH, mode='rb')
sampleRate = wavFile.getframerate()
sampleCount= wavFile.getnframes()
wavFile.close()

segueSamplesFromEnd = int(sampleRate*segueSecsFromEnd)
segueSamplesFromStart = sampleCount-segueSamplesFromEnd
introEndSamplesFromStart = int(sampleRate*introSecsFromStart)

xml = """<?xml version=\"1.0\" ?>
<cart>
    <version>0101</version>
    <title>RNH News Advert {hourTop}</title>
    <artist>Radio NewsHub</artist>
    <cutnum></cutnum>
    <clientid></clientid>
    <category>COMM</category>
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
    <posttimers><timer type="INTe">{introTime}</timer><timer type="SEG1">{segTime}</timer></posttimers>
    <url></url>
</cart>""".format(hourTop=(datetime.now()+timedelta(hours=1)).strftime("%H:00"),
                  inDate=datetime.now().strftime("%Y/%m/%d"),
                  inTime=datetime.now().strftime("%H:%M:%S"),
                  outDate=(datetime.now()+timedelta(hours=1)).strftime("%Y/%m/%d"),
                  outTime=(datetime.now()+timedelta(hours=1)).strftime("%H:%M:%S"),
                  introTime=introEndSamplesFromStart,
                  segTime=segueSamplesFromStart)

cdpFile = cdpwavefile.CDPFile()
cdpFile.ReadWaveFile(ADVERT_WAV_FILE_PATH)
cdpFile.cart.ImportXMLValues(xml)
cdpFile.WritePCMWaveFile(ADVERT_OUTPUT_META_FILE_PATH)

# And finally, import it to Myriad
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("192.168.0.4", 6950))
s.send("""AUDIOWALL IMPORTFILE "{audioFilePath}",14999,Delete\n""".format(audioFilePath=ADVERT_OUTPUT_META_FILE_PATH))
