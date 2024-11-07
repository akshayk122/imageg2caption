import os
from flask import Flask, request, redirect, url_for, render_template,send_file
from google.cloud import storage
from datetime import timedelta
import io
import mimetypes
import google.generativeai as genai
from PIL import Image
import json

app = Flask(__name__,static_folder='static')
bucket_name = 'myprojectb1'
storage_client = storage.Client()
bucket = storage_client.bucket(bucket_name)
allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
configfile="static/config.json"

with open(configfile, 'r') as file:
    data = json.load(file)
    key=data.get("API_KEY")

genai.configure(api_key=key)

# Google Cloud Storage initialization
def upload_to_gcs(file, filename):
    blob = bucket.blob(filename)
    blob.upload_from_file(file)
    return filename

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions
   
def sanitize_filename(filename):
    return filename.replace(" ", "_")

@app.route('/')
def index():
    image_links = get_gcs_images()
    return render_template('index.html', image_links=image_links)

def get_gcs_images():
    """Retrieve image file names from GCS."""
    image_links = []
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blobs = bucket.list_blobs()

    for blob in blobs:
        if allowed_file(blob.name):
            image_links.append(blob.name)
    return image_links

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files or request.files['file'].filename == '':
        return redirect('/')

    file = request.files['file']
    if file and allowed_file(file.filename):
        filename = sanitize_filename(file.filename)
        try:
            upload_to_gcs(file, filename)
            title_and_caption = generate_title_and_caption(file)
            upload_json_to_gcs(filename,title_and_caption.strip().removeprefix('```json').removesuffix('```'))
            image_urls = get_gcs_images()
            return render_template('index.html', image_links=image_urls,success="Image uploaded successfully.")
        
        except Exception as e:
            image_urls = get_gcs_images()
            return render_template('index.html', image_links=image_urls, error=str(e))
    else:
        image_urls = get_gcs_images()
        return render_template('index.html', image_links=image_urls, error=str('Invalid File Format'))

def upload_json_to_gcs(filename,title_and_caption):
     json_filename = f"{os.path.splitext(filename)[0]}.json"
     blob = bucket.blob(json_filename)
     blob.upload_from_string(
            title_and_caption,
            content_type="text/json"
        ) 

#image caption block start
def generate_title_and_caption(file):
    generation_config = {
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 64,
        "max_output_tokens": 8192,
    }
    model = genai.GenerativeModel(model_name="gemini-1.5-flash", generation_config=generation_config)
    image = Image.open(file)
    response = model.generate_content(["Generate a title and caption for this image in JSON format.", image])
    return response.text 
#image caption block end

@app.route('/images/<filename>')
def serve_image(filename):
    blob = bucket.blob(filename)

    try:
        image_data = io.BytesIO()
        blob.download_to_file(image_data)
        image_data.seek(0) 
        mimetype, _ = mimetypes.guess_type(filename)
        if not mimetype:
            mimetype = blob.content_type or 'application/octet-stream'

        return send_file(
            image_data,
            mimetype=mimetype,
            as_attachment=False,
            download_name=filename
        )

    except Exception as e:
        return f"Could not retrieve image {filename}: {str(e)}", 500

    except Exception as e:
        return f"Could not retrieve image {filename}: {str(e)}", 500

def get_json_data(json_file):
    filename = f"{os.path.splitext(json_file)[0]}.json"
    blob = bucket.blob(filename)
    try:
        json_string = blob.download_as_text()
        data = json.loads(json_string)
        description = data.get("caption")
        title=data.get("title")
        return description,title

    except Exception as e:
        return None

@app.route('/view_image/<filename>')
def view_image(filename):
    description,title=get_json_data(filename)
    return render_template('view_image.html', filename=filename,description=description,title=title)
    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
