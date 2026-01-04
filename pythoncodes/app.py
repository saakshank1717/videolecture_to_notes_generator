from flask import Flask, render_template, request, jsonify, send_file
import os
from ai_utils import transcribe_and_ocr_video, create_structured_notes, save_to_pdf

# --- Flask setup ---
app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- Route to render the Introduction page (Root URL: /) ---
# RENAMED to 'intro' and renders 'intro.html'
@app.route("/")
def intro():
    return render_template("intro.html")


# --- NEW Route for the Main Application page (URL: /app) ---
# This is the function linked by url_for('index') from intro.html
@app.route("/app")
def index():
    return render_template("index.html")


# --- Route to handle video upload & processing ---
@app.route("/upload_video", methods=["POST"])
def upload_video():
    if "video" not in request.files:
        return jsonify({"error": "No video uploaded."}), 400

    file = request.files["video"]
    if file.filename == "":
        return jsonify({"error": "No selected file."}), 400

    # Save uploaded video
    video_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(video_path)

    # Step 1: Transcribe & OCR
    transcript = transcribe_and_ocr_video(video_path)

    if transcript is None:
        return jsonify({"error": "Error processing video."}), 500

    # Step 2: Generate notes
    notes = create_structured_notes(transcript, lecture_topic="Uploaded Lecture")

    # Step 3: Save PDF
    pdf_filename = f"{os.path.splitext(file.filename)[0]}_notes.pdf"
    pdf_file = os.path.join(UPLOAD_FOLDER, pdf_filename)
    save_to_pdf(pdf_file, notes, image_path="static/lecture_image.png")  # optional image

    # Return notes and PDF path
    return jsonify({
        "notes": notes,
        "pdf_file": pdf_filename
    })


# --- Route to download PDF ---
@app.route("/download_pdf/<filename>")
def download_pdf(filename):
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return "File not found", 404


# --- Run Flask app ---
if __name__ == "__main__":
    app.run(debug=True)