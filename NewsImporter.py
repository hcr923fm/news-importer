import os
import os.path
import subprocess
import wave
from datetime import datetime, timedelta
from cdputils import cdpwavefile
import socket
from time import sleep
import pydub

FFMPEG_FILE_LIST_PATH = os.path.join(
    "C:\\Presenter Storage\\RNH Automation", "NewsFiles.txt")
NEWS_FILE_NAME_1_MIN = "C:\\Users\\hcr-myriad-server\\Dropbox\\RNH-bulletins\\news.mp3"
NEWS_FILE_NAME_2_MIN = "C:\\Users\\hcr-myriad-server\\Dropbox\\RNH-bulletins\\twominnews.mp3"
NEWS_FILE_NAME_BREAKING = "C:\\Users\\hcr-myriad-server\\Dropbox\\RNH-bulletins\\BREAKINGNEWS.mp3"
NEWS_WAV_FILE_PATH = "C:\\Presenter Storage\\RNH Automation\\RNHNews.wav"
NEWS_BUMPER_IN_FILE_PATH = "C:\\Presenter Storage\\RNH Automation\\NewsIn.wav"
NEWS_BUMPER_OUT_FILE_PATH = "C:\\Presenter Storage\\RNH Automation\\NewsOut.wav"
NEWS_WITH_OUTSTING_NOMETA_FILE_PATH = "C:\\Presenter Storage\\RNH Automation\\NewsWithOutNoMeta.wav"
NEWS_WITH_OUTSTING_WITHMETA_FILE_PATH = "C:\\Presenter Storage\\RNH Automation\\NewsWithOutMeta.wav"
NEWS_WITH_INSTING_OUTSTING_NOMETA_FILE_PATH = "C:\\Presenter Storage\\RNH Automation\\NewsWithInOutNoMeta.wav"
NEWS_WITH_INSTING_OUTSTING_WITHMETA_FILE_PATH = "C:\\Presenter Storage\\RNH Automation\\NewsWithInOutMeta.wav"


def setAudioFileMeta(input_file, output_file, set_intro=False):
    sampleRate = 0
    introSecsFromStart = 1.4
    segueSecsFromEnd = 2
    sampleCount = 0

    wavFile = wave.open(input_file, mode='rb')
    sampleRate = wavFile.getframerate()
    sampleCount = wavFile.getnframes()
    wavFile.close()

    segueSamplesFromEnd = sampleRate*segueSecsFromEnd
    segueSamplesFromStart = sampleCount-segueSamplesFromEnd
    introSamplesFromStart = round(
        sampleRate*introSecsFromStart) if set_intro else 0

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
                      outDate=(datetime.now()+timedelta(hours=1)
                               ).strftime("%Y/%m/%d"),
                      outTime=(datetime.now()+timedelta(hours=1)
                               ).strftime("%H:%M:%S"),
                      inteTime=introSamplesFromStart,
                      segTime=segueSamplesFromStart)

    cdpFile = cdpwavefile.CDPFile()
    cdpFile.ReadWaveFile(input_file)
    cdpFile.cart.ImportXMLValues(xml)
    cdpFile.WritePCMWaveFile(output_file)


NEWS_MP3_FILE_PATH = None
if os.path.exists(NEWS_FILE_NAME_BREAKING):
    NEWS_MP3_FILE_PATH = NEWS_FILE_NAME_BREAKING
elif os.path.exists(NEWS_FILE_NAME_2_MIN):
    NEWS_MP3_FILE_PATH = NEWS_FILE_NAME_2_MIN
else:
    NEWS_MP3_FILE_PATH = NEWS_FILE_NAME_1_MIN

# Now concat the files
news_in = pydub.AudioSegment.from_wav(NEWS_BUMPER_IN_FILE_PATH)
news_out = pydub.AudioSegment.from_wav(NEWS_BUMPER_OUT_FILE_PATH)
news_content = pydub.AudioSegment.from_file(NEWS_MP3_FILE_PATH, "mp3")

news_with_out_nometa = news_content.append(news_out)
news_with_in_out_nometa = news_in.append(news_with_out_nometa, 500)

# Now calculate the offset for the extro/SEG1 marker (2 secs from end)

news_with_out_nometa.export(NEWS_WITH_OUTSTING_NOMETA_FILE_PATH, "wav")
news_with_in_out_nometa.export(
    NEWS_WITH_INSTING_OUTSTING_NOMETA_FILE_PATH, "wav")

setAudioFileMeta(NEWS_WITH_OUTSTING_NOMETA_FILE_PATH,
                 NEWS_WITH_OUTSTING_WITHMETA_FILE_PATH)

setAudioFileMeta(NEWS_WITH_INSTING_OUTSTING_NOMETA_FILE_PATH,
                 NEWS_WITH_INSTING_OUTSTING_WITHMETA_FILE_PATH, True)

os.remove(NEWS_WITH_OUTSTING_NOMETA_FILE_PATH)
os.remove(NEWS_WITH_INSTING_OUTSTING_NOMETA_FILE_PATH)

# And finally, import it to Myriad
print "Importing cart 15000 (no 'IN' jingle)"
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("192.168.0.4", 6950))
s.send("""AUDIOWALL IMPORTFILE "{audioFilePath}",15000,Delete\n""".format(
    audioFilePath=NEWS_WITH_OUTSTING_WITHMETA_FILE_PATH))
s.close()

print "Waiting for Myriad..."
sleep(5)

print "Importing cart 1 (full news)"
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("192.168.0.4", 6950))
s.send("""AUDIOWALL IMPORTFILE "{audioFilePath}",1,Delete\n""".format(
    audioFilePath=NEWS_WITH_INSTING_OUTSTING_WITHMETA_FILE_PATH))
