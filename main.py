import os
from flask import Flask, request, abort, jsonify, send_from_directory
from datetime import datetime

app = Flask(__name__)
STORAGE_DIR = 'storage'

if not os.path.exists(STORAGE_DIR):
    os.makedirs(STORAGE_DIR)


@app.route('/', defaults={'path': ''}, methods=['PUT', 'GET', 'DELETE', 'HEAD'])
@app.route('/<path:path>', methods=['PUT', 'GET', 'DELETE', 'HEAD'])
def handle_file(path):
    full_path = os.path.join(STORAGE_DIR, path)

    try:
        if request.method == 'PUT':
            return upload_file(full_path)
        elif request.method == 'GET':
            return get_file_or_dir(full_path, path)
        elif request.method == 'DELETE':
            return delete_file(full_path)
        elif request.method == 'HEAD':
            return file_metadata(full_path)
    except Exception as e:
        return str(e), 500


def upload_file(full_path):
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, 'wb') as f:
        f.write(request.data)
    return '', 201


def get_file_or_dir(full_path, web_path):
    if not os.path.exists(full_path):
        abort(404)

    if os.path.isdir(full_path):
        return list_files(full_path)
    else:
        return send_file_content(full_path)


def list_files(full_path):
    files = []
    for item in os.listdir(full_path):
        item_path = os.path.join(full_path, item)
        stat = os.stat(item_path)
        files.append({
            'name': item,
            'type': 'directory' if os.path.isdir(item_path) else 'file',
            'size': stat.st_size,
            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
        })
    return jsonify(files)


def send_file_content(full_path):
    if full_path.endswith(('.txt', '.csv', '.json', '.md')):
        with open(full_path, 'r', encoding='utf-8') as f:
            return f.read()
    return send_from_directory(os.path.dirname(full_path), os.path.basename(full_path))


def delete_file(full_path):
    if not os.path.exists(full_path):
        abort(404)

    if os.path.isdir(full_path):
        os.rmdir(full_path)
    else:
        os.remove(full_path)
    return '', 204


def file_metadata(full_path):
    if not os.path.exists(full_path):
        abort(404)

    if os.path.isdir(full_path):
        return '', 200

    file_stat = os.stat(full_path)
    headers = {
        'Content-Length': str(file_stat.st_size),
        'Last-Modified': datetime.fromtimestamp(file_stat.st_mtime).strftime('%a, %d %b %Y %H:%M:%S GMT'),
        'Content-Type': 'text/plain; charset=utf-8' if full_path.endswith('.txt') else 'application/octet-stream'
    }

    response = app.response_class()
    response.headers = headers
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)