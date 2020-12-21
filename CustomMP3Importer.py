import os
import os.path
import subprocess
import wave
from datetime import datetime, timedelta
from cdputils import cdpwavefile
import socket
from time import sleep
import pydub
import sys

AUDIO_FILE_PATH = sys.argv[1]
DESTINATION_CART = sys.argv[2]
AUDIO_AS_WAV_FILE_PATH = "".join([AUDIO_FILE_PATH, ".wav"])
AUDIO_AS_WAV_META_FILE_PATH = os.path.join(os.path.dirname(AUDIO_AS_WAV_FILE_PATH), "".join(
    [os.path.basename(AUDIO_AS_WAV_FILE_PATH).split(".")[0], "-meta-", ".wav"]))


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
    segueSamplesFromStart = int(round(sampleCount-segueSamplesFromEnd))
    introSamplesFromStart = int(round(
        sampleRate*introSecsFromStart)) if set_intro else 0

# Still set type as NEWS?
    xml = """<?xml version=\"1.0\" ?>
    <cart>
        <version>0101</version>
        <title>{title}</title>
        <artist></artist>
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
        <posttimers><timer type="SEG1">{segTime}</timer><timer type="INTe">{inteTime}</timer></posttimers>
        <url></url>
    </cart>""".format(title=os.path.basename(input_file),
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


news_content = pydub.AudioSegment.from_file(AUDIO_FILE_PATH, "mp3")

# Now calculate the offset for the extro/SEG1 marker (2 secs from end)

news_content.export(AUDIO_AS_WAV_FILE_PATH, "wav")

setAudioFileMeta(AUDIO_AS_WAV_FILE_PATH,
                 AUDIO_AS_WAV_META_FILE_PATH)

os.remove(AUDIO_AS_WAV_FILE_PATH)

# And finally, import it to Myriad
print "Importing to cart {0}".format(DESTINATION_CART)
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("192.168.0.4", 6950))
s.send("""AUDIOWALL IMPORTFILE "{audioFilePath}",{destCart},Delete\n""".format(
    audioFilePath=AUDIO_AS_WAV_META_FILE_PATH, destCart=DESTINATION_CART))
s.close()
