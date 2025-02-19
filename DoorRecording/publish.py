import cv2
import os
import face_recognition
import time
import sounddevice as sd
import soundfile as sf
import numpy as np
import ffmpeg
# Manually specify the path to the Haarcascade XML file
face_cascade = cv2.CascadeClassifier('/usr/share/opencv4/haarcascades/haarcascade_frontalface_default.xml')

# Initialize video capture
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Could not open video device")
    exit()

# Video recording parameters
is_recording = False
video_writer = None
buffer_time = 15  # Stop recording if face is out of the screen for 15 seconds
last_event_time = 0
filename = ""

# Audio recording parameters
audio_frames = []
sample_rate = 44100  # Standard sample rate for audio
channels = 2  # Stereo audio

# Retrieve FPS and ensure a valid value
fps = cap.get(cv2.CAP_PROP_FPS)
fps = 10  # Default to 20 FPS if invalid
# Try using 'MJPG' codec if 'XVID' causes issues
fourcc = cv2.VideoWriter_fourcc(*'MJPG')

# Path to the folder containing images of known persons
known_faces_folder = "FACES"

# Check if the known_faces folder exists
if not os.path.exists(known_faces_folder):
    print(f"Error: The folder '{known_faces_folder}' does not exist. Please create it and add images of known individuals.")
    exit()

# Load known faces
known_face_encodings = []
known_face_names = []

# Load known faces and their names
for image_name in os.listdir(known_faces_folder):
    image_path = os.path.join(known_faces_folder, image_name)
    try:
        image = face_recognition.load_image_file(image_path)
        face_encodings = face_recognition.face_encodings(image)
        if len(face_encodings) > 0:
            face_encoding = face_encodings[0]
            known_face_encodings.append(face_encoding)
            known_face_names.append(os.path.splitext(image_name)[0])
        else:
            print(f"No face found in {image_name}. Skipping this image.")
    except Exception as e:
        print(f"Error processing {image_name}: {e}")

if not known_face_encodings:
    print("No valid face encodings found in the known_faces folder. Please add valid images.")
    exit()

# Path to the folder containing parcel templates
parcel_templates_folder = "parcel_templates"

# Check if the parcel_templates folder exists
if not os.path.exists(parcel_templates_folder):
    print(f"Error: The folder '{parcel_templates_folder}' does not exist. Please create it and add images of parcels.")
    exit()

# Load parcel templates
parcel_templates = []
for image_name in os.listdir(parcel_templates_folder):
    image_path = os.path.join(parcel_templates_folder, image_name)
    template = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if template is not None:
        parcel_templates.append(template)
    else:
        print(f"Error loading template: {image_name}")

if not parcel_templates:
    print("No valid parcel templates found. Please add valid images.")
    exit()

def recognize_faces(frame, known_face_encodings, known_face_names):
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb_frame)
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

    for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
        matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
        name = "Unknown"

        if True in matches:
            first_match_index = matches.index(True)
            name = known_face_names[first_match_index]

            # Overwrite the recognized name to "trigger.txt"
            with open("trigger.txt", "w") as file:
                file.write(f"{name}\n")

        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
        cv2.putText(frame, name, (left, bottom + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

    return frame

def detect_parcels(frame):
    """Detect parcels using template matching."""
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    for template in parcel_templates:
        result = cv2.matchTemplate(gray_frame, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        # If the match is good enough, draw a bounding box
        if max_val > 0.7:  # Adjust this threshold as needed
            h, w = template.shape
            top_left = max_loc
            bottom_right = (top_left[0] + w, top_left[1] + h)
            cv2.rectangle(frame, top_left, bottom_right, (255, 0, 0), 2)
            cv2.putText(frame, "Parcel", (top_left[0], top_left[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)

    return frame

def record_audio():
    """Record audio using sounddevice."""
    print("Recording audio...")
    return sd.rec(int(buffer_time * sample_rate), samplerate=sample_rate, channels=channels, dtype='float32')


def combine_audio_video(video_file, audio_file, output_file):
    """Combine video and audio using ffmpeg-python."""
    input_video = ffmpeg.input(video_file)
    input_audio = ffmpeg.input(audio_file)
    
    ffmpeg.output(input_video, input_audio, output_file, vcodec='libx264', acodec='aac').run()

while True:
    ret, frame = cap.read()
    if not ret:
        print("Error: Could not read frame from camera")
        break

    # Detect faces
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

    # Recognize faces
    if len(faces) > 0:
        frame = recognize_faces(frame, known_face_encodings, known_face_names)

        # Start recording if not already recording
        if not is_recording:
            is_recording = True
            last_event_time = time.time()
            filename = f"recording_{int(last_event_time)}.avi"
            height, width = frame.shape[:2]
            video_writer = cv2.VideoWriter(filename, fourcc, int(fps), (width, height))
            if not video_writer.isOpened():
                print("Error: VideoWriter failed to open.")
                is_recording = False
                continue
            print(f"Started recording: {filename}")

            # Start audio recording
            audio_frames = record_audio()

        # Update the last event time
        last_event_time = time.time()

    # Detect parcels
    frame = detect_parcels(frame)

    # If recording, write the frame to the video file
    if is_recording and video_writer is not None:
        video_writer.write(frame)

        # Stop recording if the buffer time has passed since the last face detection
        if time.time() - last_event_time > buffer_time:
            print(f"Stopped recording. Saved: {filename}")
            video_writer.release()
            video_writer = None
            is_recording = False

            # Stop audio recording and save to file
            sd.stop()
            audio_file = f"audio_{int(last_event_time)}.wav"
            sf.write(audio_file, np.concatenate(audio_frames), sample_rate)

            # Combine audio and video
            output_file = f"final_{int(last_event_time)}.mp4"
            combine_audio_video(filename, audio_file, output_file)

            # Clear the content of "trigger.txt" after stopping recording
            with open("trigger.txt", "w") as file:
                file.write("")

    # Display the frame
    cv2.imshow('Face and Parcel Detection Feed', frame)

    # Exit on 'q' key press
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

if is_recording and video_writer is not None:
    video_writer.release()
cap.release()
cv2.destroyAllWindows()
