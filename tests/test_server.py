import os
import json
from flask import Flask, jsonify

# Test endpoint to check file reading
app = Flask(__name__)

@app.route('/test_file_content')
def test_file_content():
    filename = 'epicrbot20099gmail.com_77b3a162-0548-461b-9194-06e7b4f193d7_Testassinmen.txt'
    uploads_dir = '/workspaces/Hackathon-Project/uploads'
    file_path = os.path.join(uploads_dir, filename)
    
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return jsonify({
                'status': 'success',
                'filename': filename,
                'content': content,
                'length': len(content)
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'error': str(e)
            })
    else:
        return jsonify({
            'status': 'error',
            'error': 'File not found'
        })

if __name__ == '__main__':
    app.run(port=5001)
