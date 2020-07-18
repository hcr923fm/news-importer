from subprocess import Popen
import os
import wave
import pydub

YTDL_PATH = "C:\\Presenter Storage\\RNH Automation\\youtube-dl.exe"
CHAT_SHOW_DL_FILE_PATH = "C:\\Presenter Storage\\RNH Automation\\ChatShowFull.aac"
CHAT_SHOW_DL_WAV_FILE_PATH = "C:\\Presenter Storage\\RNH Automation\\ChatShowFull.wav"
CHAT_SHOW_TRIM_START_FILE_PATH = "C:\\Presenter Storage\\RNH Automation\\ChatShowTrimStart.wav"
CHAT_SHOW_TRIM_START_END_FILE_PATH = "C:\\Presenter Storage\\RNH Automation\\ChatShowTrimStartEnd.wav"

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
print "loaded audio, searching for silence"
split = pydub.silence.split_on_silence(audio, 3000, -50, 500, 250)

normalized = pydub.effects.normalize(split[0],)
normalized.export(CHAT_SHOW_TRIM_START_END_FILE_PATH, "wav")

os.remove(CHAT_SHOW_DL_FILE_PATH)
os.remove(CHAT_SHOW_DL_WAV_FILE_PATH)
