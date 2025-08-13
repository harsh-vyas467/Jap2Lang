import io
import PyPDF2
from flask import Flask, request, send_file, render_template
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from deep_translator import GoogleTranslator

app = Flask(__name__)

# List of supported languages for the dropdown menu
supported_languages = {
    'English': 'en',
    'Japanese': 'ja',
    'Spanish': 'es',
    'French': 'fr',
    'German': 'de',
    'Chinese (Simplified)': 'zh-CN',
    'Korean': 'ko',
    'Russian': 'ru',
    'Portuguese': 'pt'
}

@app.route('/')
def index():
    return render_template('pdf_input_multi_lang.html', languages=supported_languages)

@app.route('/translate', methods=['POST'])
def translate_pdf():
    # 1. Check for file upload and selected language
    if 'file' not in request.files:
        return "No file part", 400
    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400

    target_lang_code = request.form.get('language')
    if not target_lang_code or target_lang_code not in supported_languages.values():
        return "Invalid or no target language selected", 400

    if file:
        # 2. Extract text from the PDF
        try:
            pdf_reader = PyPDF2.PdfReader(file)
            full_text = ""
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                full_text += page.extract_text()
        except Exception as e:
            return f"Error reading PDF file: {e}", 500

        # 3. Translate the extracted text using deep-translator
        try:
            # Source language is hardcoded to Japanese ('ja') for the purpose of this manual
            translated_text = GoogleTranslator(source='ja', target=target_lang_code).translate(full_text)
        except Exception as e:
            return f"Error during translation: {e}", 500

        # 4. Create a new PDF with the translated text
        output_buffer = io.BytesIO()
        p = canvas.Canvas(output_buffer, pagesize=letter)
        
        textobject = p.beginText()
        textobject.setTextOrigin(10, 750)
        textobject.setFont("Helvetica", 12)

        lines = translated_text.split('\n')
        y_position = 750
        for line in lines:
            if y_position < 50:
                p.drawText(textobject)
                p.showPage()
                textobject = p.beginText()
                textobject.setTextOrigin(10, 750)
                textobject.setFont("Helvetica", 12)
                y_position = 750
            
            textobject.textLine(line)
            y_position -= 14
        
        p.drawText(textobject)
        p.save()
        output_buffer.seek(0)

        # 5. Send the new PDF as a downloadable response
        return send_file(
            output_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'translated_document_{target_lang_code}.pdf'
        )

if __name__ == '__main__':
    app.run(debug=True)