import os
from flask import Flask, render_template, request, send_file
from werkzeug.utils import secure_filename
import tempfile
import PyPDF2
import google.generativeai as genai
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# ----------------------
# CONFIGURATION
# ----------------------
GEMINI_API_KEY = "<gemini_api_key"  
if not GEMINI_API_KEY:
    raise ValueError("Please set GEMINI_API_KEY as environment variable")

# Configure Gemini client
genai.configure(api_key=GEMINI_API_KEY)

app = Flask(__name__)

# Allowed languages (name → code)
LANGUAGES = {
    "English": "English",
    "Spanish": "Spanish",
    "French": "French",
    "German": "German",
    "Chinese (Simplified)": "Simplified Chinese",
    "Korean": "Korean",
    "Hindi": "Hindi",
}

# ----------------------
# GEMINI TRANSLATION FUNCTION
# ----------------------
def translate_text(text, target_language):
    prompt = f"Translate the following Japanese text to {target_language}:\n\n{text}"

    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)

    return response.text.strip()

# ----------------------
# PDF TEXT EXTRACTION
# ----------------------
def extract_text_from_pdf(pdf_path):
    text = ""
    with open(pdf_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text.strip()

# ----------------------
# CREATE TRANSLATED PDF
# ----------------------
def create_translated_pdf(text, output_path):
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4

    y_position = height - 50
    for line in text.split("\n"):
        c.drawString(50, y_position, line)
        y_position -= 15
        if y_position < 50:
            c.showPage()
            y_position = height - 50
    c.save()

# ----------------------
# ROUTES
# ----------------------
@app.route("/")
def index():
    return render_template("index.html", languages=LANGUAGES)

@app.route("/translate", methods=["POST"])
def translate_pdf():
    target_language = request.form.get("language")
    file = request.files.get("file")

    if not file or not target_language:
        return "Please upload a PDF and choose a language", 400

    filename = secure_filename(file.filename)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
        file.save(temp_pdf.name)
        pdf_path = temp_pdf.name

    extracted_text = extract_text_from_pdf(pdf_path)
    if not extracted_text:
        return "No text found in PDF", 400

    translated_text = translate_text(extracted_text, target_language)

    output_pdf_path = os.path.join(tempfile.gettempdir(), "translated.pdf")
    create_translated_pdf(translated_text, output_pdf_path)

    return send_file(output_pdf_path, as_attachment=True, download_name="translated.pdf")

# ----------------------
# RUN APP
# ----------------------
if __name__ == "__main__":
    app.run(debug=True)
