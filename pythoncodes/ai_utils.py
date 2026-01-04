import whisper
import google.generativeai as genai
import os
import subprocess
import cv2
import pytesseract
import tempfile
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet

# --- Configuration ---
gemini_api_key = "AIzaSyCKVeXMH733ZK5F_Yaz2wrcVeKLU2T_Dfc"
genai.configure(api_key=gemini_api_key)

# Configure Tesseract path
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


# --- Step 1: Combined Transcription and OCR ---
def transcribe_and_ocr_video(file_path):
    try:
        temp_dir = tempfile.mkdtemp()
        audio_file_path = os.path.join(temp_dir, "extracted_audio.mp3")

        # Extract audio using FFmpeg
        command_audio = ['ffmpeg', '-i', file_path, '-q:a', '0', '-map', 'a', audio_file_path, '-y']
        subprocess.run(command_audio, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Transcribe audio with Whisper
        whisper_model = whisper.load_model("tiny")
        audio_transcript = whisper_model.transcribe(audio_file_path, fp16=False)

        # OCR from video frames
        ocr_text = []
        video = cv2.VideoCapture(file_path)
        fps = video.get(cv2.CAP_PROP_FPS)
        frame_interval_seconds = 5
        frame_count = 0

        while True:
            success, frame = video.read()
            if not success:
                break

            if frame_count % (fps * frame_interval_seconds) == 0:
                try:
                    text_from_frame = pytesseract.image_to_string(frame)
                    if text_from_frame.strip():
                        ocr_text.append(f"Text from frame at {frame_count / fps:.2f}s:\n{text_from_frame}")
                except Exception as e:
                    print(f"Error during OCR on frame {frame_count}: {e}")

            frame_count += 1

        video.release()
        full_text = audio_transcript['text'] + "\n\n" + " ".join(ocr_text)

        os.remove(audio_file_path)
        os.rmdir(temp_dir)

        return full_text

    except Exception as e:
        print(f"Error in transcribe_and_ocr_video: {e}")
        return None


# --- Step 2: Summarization with GenAI ---
def create_structured_notes(transcript, lecture_topic="General Lecture"):
    if not transcript:
        return "No transcript provided to summarize."

    prompt = f"""
    **STRICT INSTRUCTION:** Generate ONLY the structured lecture notes and mind map as outlined below. DO NOT include these instructions, the list of rules (1-5), the Transcript section, or any conversational text.

    **LECTURE NOTES RULES:**
    1. Use plain text only. Do not use #, *, or any markdown symbols.
    2. Organize the lecture into subtopics listed as:
       a) First subtopic
       b) Second subtopic
       ...
    3. For each subtopic, include:
       - Definition: A concise explanation of the concept.
       - Key Points: 3–4 important points, each as a separate nested item.
       - Example: One example to clarify the concept.
       - Application: One real-world use or application (if applicable).
    4. Keep explanations simple, clear, and easy to understand.

    **MIND MAP RULES:**
    5. After the notes, create a mind map of the entire topic using `------->` to indicate hierarchy:
       - The main topic should be at the top.
       - Subtopics should branch from the main topic.
       - Definition, key points, example, and application should branch from their respective subtopics.
       - Ensure proper indentation so the structure is clear and hierarchical.
       - Use the following nesting style:
        Main Topic
    |
    |---------> Subtopic 1
    |            |
    |            |---------> Definition: very small 
    |            |---------> Key Points:|---------> Points 
    |             |---------> Example: ...2-5 words 
    |            |---------> Application: .2-5 words. 
    |         
    |                  
    |
    |---------> Subtopic n(same as subtopic 1)  
            
Transcript:
---
{transcript}
---

    """

    try:
        # Updated model
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"An error occurred with the Gemini API: {e}"

# --- Step 3: Save to PDF ---
def save_to_pdf(filename, notes, image_path=None):
    doc = SimpleDocTemplate(filename, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    styles = getSampleStyleSheet()
    story = []

    # Optional image at beginning
    if image_path and os.path.exists(image_path):
        try:
            img = Image(image_path, width=400, height=200)
            story.append(img)
            story.append(Spacer(1, 24))
        except Exception as e:
            print(f"Could not add image: {e}")

    # Add notes text
    for line in notes.split("\n"):
        if line.strip():
            p = Paragraph(line.strip(), styles['Normal'])
            story.append(p)

    doc.build(story)
