import pyaudio
import wave
import os
import pygame
import logging

class AudioUtils:
    def __init__(self, speech_dir: str = "speech/"):
        self.logger = logging.getLogger(__name__)
        self.speech_dir = speech_dir
        self.chunk = 1024
        self.sample_format = pyaudio.paInt16
        self.channels = 1
        self.fs = 44100  # Sample rate
        pygame.mixer.init()

    def record_audio(self, output_file: str, duration: int = 5) -> str:
        output_path = os.path.join(self.speech_dir, output_file)
        p = pyaudio.PyAudio()
        stream = p.open(format=self.sample_format,
                        channels=self.channels,
                        rate=self.fs,
                        frames_per_buffer=self.chunk,
                        input=True)
        frames = []

        self.logger.info(f"Recording audio for {duration} seconds...")
        for _ in range(0, int(self.fs / self.chunk * duration)):
            data = stream.read(self.chunk)
            frames.append(data)

        stream.stop_stream()
        stream.close()
        p.terminate()

        wf = wave.open(output_path, "wb")
        wf.setnchannels(self.channels)
        wf.setsampwidth(p.get_sample_size(self.sample_format))
        wf.setframerate(self.fs)
        wf.writeframes(b"".join(frames))
        wf.close()

        self.logger.info(f"Saved recorded audio to: {output_path}")
        return output_path

    def play_audio(self, audio_path: str):
        try:
            self.logger.info(f"Playing audio: {audio_path}")
            pygame.mixer.music.load(audio_path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
        except Exception as e:
            self.logger.error(f"Failed to play audio: {str(e)}")

    def delete_audio(self, audio_path: str):
        try:
            if os.path.exists(audio_path):
                os.remove(audio_path)
                self.logger.info(f"Deleted audio file: {audio_path}")
        except Exception as e:
            self.logger.error(f"Failed to delete audio file: {str(e)}")