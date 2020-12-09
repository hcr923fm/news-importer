import os
import socket
import wave
from datetime import datetime, timedelta
from subprocess import Popen
import pydub
from cdputils import cdpwavefile

YTDL_PATH = "C:\\Presenter Storage\\RNH Automation\\youtube-dl.exe"
CHAT_SHOW_DL_FILE_PATH = "C:\\Presenter Storage\\RNH Automation\\ChatShowFull.aac"
CHAT_SHOW_DL_WAV_FILE_PATH = "C:\\Presenter Storage\\RNH Automation\\ChatShowFull.wav"
CHAT_SHOW_TRIMMED_PATH = "C:\\Presenter Storage\\RNH Automation\\RNHNewsChat.wav"
CHAT_SHOW_TRIMMED_META_PATH = "C:\\Presenter Storage\\RNH Automation\\ChatShowTrimStartEnd.wav"


def setAudioFileMeta(input_file, output_file, set_intro=False):
    sampleRate = 0
    introSecsFromStart = 0.5
    segueSecsFromEnd = 0.5
    sampleCount = 0

    wavFile = wave.open(input_file, mode='rb')
    sampleRate = wavFile.getframerate()
    sampleCount = wavFile.getnframes()
    wavFile.close()

    segueSamplesFromEnd = sampleRate*segueSecsFromEnd
    segueSamplesFromStart = int(round(sampleCount-segueSamplesFromEnd))
    introSamplesFromStart = int(round(
        sampleRate*introSecsFromStart)) if set_intro else 0

    xml = """<?xml version=\"1.0\" ?>
    <cart>
        <version>0101</version>
        <title>RNH News Chat</title>
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
        <posttimers><timer type="SEG1">{segTime}</timer><timer type="INTe">{inteTime}</timer></posttimers>
        <url></url>
    </cart>""".format(inDate=datetime.now().strftime("%Y/%m/%d"),
                      inTime=datetime.now().strftime("%H:%M:%S"),
                      outDate=(datetime.now()+timedelta(hours=72)
                               ).strftime("%Y/%m/%d"),
                      outTime=(datetime.now()+timedelta(hours=72)
                               ).strftime("%H:%M:%S"),
                      inteTime=introSamplesFromStart,
                      segTime=segueSamplesFromStart)

    cdpFile = cdpwavefile.CDPFile()
    cdpFile.ReadWaveFile(input_file)
    cdpFile.cart.ImportXMLValues(xml)
    cdpFile.WritePCMWaveFile(output_file)


Popen([
    YTDL_PATH,
    "-x",
    "--audio-format", "aac",
    "--playlist-items", "1,2",
    "--match-title", "news chat",
    "-o", CHAT_SHOW_DL_FILE_PATH,
    "https://www.youtube.com/channel/UClQVurcNqp0BIxbKH2kJojg/videos"
]).wait()

Popen([
    "ffmpeg",
    "-y",
    "-i", CHAT_SHOW_DL_FILE_PATH,
    "-c:a", "pcm_s16le",
    "-ac", "2",
    "-ar", "44100",
    CHAT_SHOW_DL_WAV_FILE_PATH
]).wait()

audio = pydub.AudioSegment.from_wav(CHAT_SHOW_DL_WAV_FILE_PATH)

print "Loaded audio, searching for silence"
split = pydub.silence.split_on_silence(audio, 3000, -50, 100, 250)

print "Normalizing audio"
normalized = pydub.effects.normalize(split[0],)

print "Saving chat show"
normalized.export(CHAT_SHOW_TRIMMED_PATH, "wav")

os.remove(CHAT_SHOW_DL_FILE_PATH)
os.remove(CHAT_SHOW_DL_WAV_FILE_PATH)

print "Setting Myriad Metadata"
setAudioFileMeta(CHAT_SHOW_TRIMMED_PATH, CHAT_SHOW_TRIMMED_META_PATH, True)

print "Importing into Myriad"
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("192.168.0.4", 6950))
s.send("""AUDIOWALL IMPORTFILE "{audioFilePath}",{cartNum},Delete\n""".format(
    audioFilePath=CHAT_SHOW_TRIMMED_META_PATH, cartNum=14995))
