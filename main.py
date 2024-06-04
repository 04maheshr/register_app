from flask import Flask, render_template, request, jsonify, send_file
import os
import pdfplumber
import pandas as pd
import ast
import shutil

app = Flask(__name__)

def extract_borderless_tables(page):
    lines = page.lines
    words = page.extract_words()
    data = []
    current_row = []
    last_bottom = None

    for word in words:
        if last_bottom is None or abs(word['bottom'] - last_bottom) < 5:
            current_row.append(word['text'])
        else:
            data.append(current_row)
            current_row = [word['text']]
        last_bottom = word['bottom']
    data.append(current_row)

    return data

def extract_marks_from_pdf(pdf_path, reg_numbers):
    marks_dict = {}
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            tables = page.extract_tables()
            if not tables:
                tables = [extract_borderless_tables(page)]
            for table in tables:
                df = pd.DataFrame(table)
                for reg_number in reg_numbers:
                    for index, row in df.iterrows():
                        if reg_number in row.values:
                            reg_index = row.values.tolist().index(reg_number)
                            if reg_index + 1 < len(row):
                                marks_dict[reg_number] = row.iloc[reg_index + 1]
    return marks_dict

def process_pdfs_in_folder(folder_path, reg_numbers):
    results = {}
    pdf_files = [f for f in os.listdir(folder_path) if f.endswith('.pdf')]
    for filename in pdf_files:
        pdf_path = os.path.join(folder_path, filename)
        marks = extract_marks_from_pdf(pdf_path, reg_numbers)
        for reg_number, marks_value in marks.items():
            if reg_number not in results:
                results[reg_number] = {}
            results[reg_number][filename] = marks_value
    return results

@app.route('/')
def index():
    return render_template('1.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    registration_numbers = request.form.get('regNumbers')
    uploaded_files = request.files.getlist('pdfFiles')

    if not registration_numbers:
        return jsonify({'success': False, 'message': 'No registration numbers provided.'})
    
    if not uploaded_files:
        return jsonify({'success': False, 'message': 'No files uploaded.'})
    
    reg_numbers = ast.literal_eval(registration_numbers)
    
    upload_dir = './uploads'
    results_dir = './results'
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
    
    file_info = []
    for file in uploaded_files:
        file_path = os.path.join(upload_dir, file.filename)
        
        try:
            file.save(file_path)
            saved_file_size = os.path.getsize(file_path)
            file_info.append({'name': file.filename, 'size': saved_file_size})
        except Exception as e:
            return jsonify({'success': False, 'message': f'Error saving file {file.filename}'})
    
    results = process_pdfs_in_folder(upload_dir, reg_numbers)
    df = pd.DataFrame(results).fillna('Not Found')
    df_transposed = df.transpose()
    output_filename = 'results.xlsx'
    output_path = os.path.join(results_dir, output_filename)
    df_transposed.to_excel(output_path, index=True)
    
    # Return the download URL for the Excel file
    response = {
        'success': True,
        'message': 'Files uploaded successfully.',
        'files': file_info,
        'download_url': f'/download/{output_filename}'
    }
    for file in uploaded_files:
        os.remove(os.path.join(upload_dir, file.filename))
    
    return jsonify(response)

@app.route('/download/<filename>')
def download_file(filename):
    results_dir = './results'
    file_path = os.path.join(results_dir, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        return "File not found", 404

if __name__ == '__main__':
    app.run(debug=True)