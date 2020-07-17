from subprocess import Popen
import os
import wave

YTDL_PATH = "C:\\Presenter Storage\\RNH Automation\\youtube-dl.exe"
CHAT_SHOW_DL_FILE_PATH = "C:\\Presenter Storage\\RNH Automation\\ChatShowFull.opus"
CHAT_SHOW_DL_WAV_FILE_PATH = "C:\\Presenter Storage\\RNH Automation\\ChatShowFull.wav"
CHAT_SHOW_TRIM_START_FILE_PATH = "C:\\Presenter Storage\\RNH Automation\\ChatShowTrimStart.wav"
CHAT_SHOW_TRIM_START_END_FILE_PATH = "C:\\Presenter Storage\\RNH Automation\\ChatShowTrimStartEnd.wav"

Popen([
    YTDL_PATH,
    "-x",
    "--audio-format", "best",
    "--playlist-items", "1",
    "-o", CHAT_SHOW_DL_FILE_PATH,
    "https://www.youtube.com/channel/UClQVurcNqp0BIxbKH2kJojg/videos"
]).wait()

Popen([
    "ffmpeg",
    "-y",
    "-i", CHAT_SHOW_DL_FILE_PATH,
    "-c:a", "pcm_s16le",
    CHAT_SHOW_DL_WAV_FILE_PATH
]).wait()

wav = wave.open(CHAT_SHOW_DL_WAV_FILE_PATH, "r")
silenceThresholdSecs = 3
startPosSecs = 0
foundStartPos = False
currentPosInFrames = 0
while(not foundStartPos):
    chunk = wav.readframes(500)
    for i in xrange(len(chunk)):
        if ord(chunk[i]) != 0:
            startPos = (currentPosInFrames + i)/float(wav.getframerate())
            foundStartPos = True
            break
    currentPosInFrames += 500

print "\r\nGot audio start position: {startPos}".format(startPos=startPos)

total_duration = wav.getnframes()/wav.getframerate()
wav.close()

Popen([
    "ffmpeg",
    "-y",
    "-ss", "{0}s".format(startPos),
    "-i", CHAT_SHOW_DL_WAV_FILE_PATH,
    CHAT_SHOW_TRIM_START_FILE_PATH
]).wait()

trimmed_duration = total_duration-10
print total_duration, trimmed_duration

Popen([
    "ffmpeg",
    "-y",
    "-to", "{dur}s".format(dur=total_duration),
    "-i", CHAT_SHOW_TRIM_START_FILE_PATH,
    CHAT_SHOW_TRIM_START_END_FILE_PATH
]).wait()


os.remove(CHAT_SHOW_DL_FILE_PATH)
os.remove(CHAT_SHOW_DL_WAV_FILE_PATH)
os.remove(CHAT_SHOW_TRIM_START_FILE_PATH)
