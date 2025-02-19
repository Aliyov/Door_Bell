from gtts import gTTS
import os
import sys
import playsound
import time

def read_text_from_file(file_path):
    """Reads text from a file."""
    if not os.path.exists(file_path):
        print(f"Error: File not found -> {file_path}")
        return None

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read().strip()
        if not text:
            print("Error: The file is empty.")
            return None
        return text
    except Exception as e:
        print(f"An error occurred while reading the file: {e}")
        return None

def extract_object_message(text, trigger):
    """Extracts the message for a specific object (trigger)."""
    lines = text.splitlines()
    object_found = False
    message = []

    for line in lines:
        if line.startswith("Object:"):
            # Check if the current object matches the trigger
            if trigger.lower() in line.lower():
                object_found = True
            else:
                # Stop if we encounter the next object
                if object_found:
                    break
        elif object_found:
            # Collect the message under the object
            message.append(line.strip())

    return " ".join(message) if message else None

def text_to_speech(text):
    """Converts text to speech using Google Text-to-Speech (gTTS)."""
    tts = gTTS(text, lang='en', slow=False)
    temp_audio = "temp_audio.mp3"
    tts.save(temp_audio)
    playsound.playsound(temp_audio)
    os.remove(temp_audio)

def main():
    """Main function to read a file and convert text to speech based on a trigger."""
    if len(sys.argv) < 2:
        print("Usage: python script.py [file_path]")
        print("Ex: python script.py tg_messages_pool.txt")
        return

    # Get the content of the trigger file (e.g., trigger.txt)
    trigger_file = "../DoorRecording/trigger.txt"
    file_path = sys.argv[1]  # 'tg_messages_pool.txt'

    while True:
        # Check the trigger file
        trigger = read_text_from_file(trigger_file)

        if not trigger:
            print(f"Empty trigger file. Retry in 5 secs...")
            time.sleep(5)  # Wait for 5 seconds before retrying
            continue  # Skip the rest of the loop and re-check the trigger file

        print(f"Trigger read from {trigger_file}: {trigger}")

        text = read_text_from_file(file_path)

        if text:
            print(f"Reading file: {file_path}")
            message = extract_object_message(text, trigger)

            if message:
                print(f"Trigger '{trigger}' found. Speaking the message:")
                print(message)
                text_to_speech(message)
                print("Retry in 20 secs...")
                time.sleep(20)  # Wait for 20 seconds after a successful speech

                # After waiting, check the trigger file again
                trigger = read_text_from_file(trigger_file)
                if not trigger:
                    print("Trigger file is now empty. Waiting 5 seconds before retrying...")
                    time.sleep(5)  # Wait for 5 seconds if the trigger file is empty
            else:
                print(f"No message found for trigger '{trigger}'.")
                print("Waiting for 5 seconds before retrying...")
                time.sleep(5)  # Wait for 5 seconds if no message was found
        else:
            print("File is empty or couldn't be read. Waiting for 5 seconds before retrying...")
            time.sleep(5)  # Wait for 5 seconds if the file is empty or couldn't be read
if __name__ == "__main__":
    main()

