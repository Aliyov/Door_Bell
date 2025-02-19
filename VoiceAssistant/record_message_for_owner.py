import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
import subprocess
import time
import os
import wave
import json
from vosk import Model, KaldiRecognizer

# Function to generate a unique filename
def get_unique_filename(base_name, extension):
    counter = 1
    while True:
        filename = f"{base_name}_{counter}.{extension}"
        if not os.path.exists(filename):
            return filename
        counter += 1

# Function to play an audio file using ffmpeg
def play_audio(file_path):
    print(f"Playing {file_path}...")
    subprocess.run(["ffplay", "-nodisp", "-autoexit", file_path])

# Function to record audio
def record_audio(duration, sample_rate=16000, output_file="output.wav"):
    print("Recording...")
    
    # Record audio
    audio = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype=np.int16)
    sd.wait()  # Wait until recording is finished
    
    # Save the recording to a file
    write(output_file, sample_rate, audio)
    print(f"Recording saved to {output_file}")

# Function to convert speech to text
def speech_to_text(input_wav, model_path, output_txt):
    # Load the Vosk model
    if not os.path.exists(model_path):
        print(f"Model path '{model_path}' does not exist.")
        return
    model = Model(model_path)

    # Open the .wav file
    with wave.open(input_wav, "rb") as wf:
        if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getframerate() not in [8000, 16000]:
            print("Audio file must be WAV format, mono, 16-bit, and 8kHz or 16kHz.")
            return

        # Initialize the recognizer
        recognizer = KaldiRecognizer(model, wf.getframerate())

        # Process the audio file
        results = []
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                text = result.get("text", "")
                if text:
                    results.append(text)

        # Get the final result
        final_result = json.loads(recognizer.FinalResult())
        text = final_result.get("text", "")
        if text:
            results.append(text)

        # Save the text to a file
        with open(output_txt, "w") as f:
            f.write(" ".join(results))
        print(f"Speech-to-text result saved to {output_txt}")

# Main function
def main():
    # Set recording duration (20 seconds)
    recording_duration = 20  # seconds
    
    # Generate unique filenames
    output_wav = get_unique_filename("output", "wav")
    output_txt = get_unique_filename("output", "txt")
    
    # Path to the Vosk model
    model_path = "vosk-model-small-en-us-0.15"  # Replace with your model path
    
    # Play the assistant start audio
    play_audio("assistant_start.mp3")
    
    # Wait for a short delay (optional)
    time.sleep(1)  # 1-second delay before recording starts
    
    # Record audio
    record_audio(recording_duration, output_file=output_wav)
    
    # Play the assistant end audio
    play_audio("assistant_end.mp3")
    
    # Convert speech to text
    speech_to_text(output_wav, model_path, output_txt)



if __name__ == "__main__":
    main()
