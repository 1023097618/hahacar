

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask import send_from_directory

from main2 import process_video
import os

app = Flask(__name__)
CORS(app)

# 设置文件上传的目录和最大文件大小
app.config['UPLOAD_FOLDER'] = 'static/uploads/videos/'
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024  # 限制最大上传文件大小为20MB

#配置静态文件服务，以便前端可以访问上传的视频文件
upload_folder = app.config['UPLOAD_FOLDER']

# 配置 Flask 路由来提供静态文件服务
#这里加不加static都可以，但要和下面返回的data中的url保持一致，videourl依赖此服务来访问文件
#返回的是该目录下的对应文件
@app.route('/api/static/uploads/videos/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/')
def index():
    return jsonify({
        "code": "200",
        "data": {},
        "msg": "Welcome！"
    }), 200


@app.route('/api/storage/videoupload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:  # 检查请求中是否有文件
        return jsonify({
            "code": "400",
            "data": {},
            "msg": "No File！"
        }), 400

    file = request.files['file']

    if file.filename == '':  # 检查文件名是否为空
        return jsonify({
            "code": "400",
            "data": {},
            "msg": "No File Name！"
        }), 400


    # if not os.path.exists(upload_folder):
    #     os.makedirs(upload_folder)
    # 保存文件到指定目录
    file.save(f"{app.config['UPLOAD_FOLDER']}{file.filename}")

    #构建要喂给yolo的视频路径
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)

    # 调用process_video函数对视频进行处理
    try:
        process_video(file_path)  # 传入视频文件路径
    except Exception as e:
        return jsonify({
            "code": "500",
            "data": {},
            "msg": f"Video processing failed: {str(e)}"
        }), 500

    #处理完成的视频文件还没保存本地
    return jsonify({
        "code": "200",
        "data": {
            "videourl": f"http://localhost:8081/static/processed/videos/{file.filename}"  #可以直接访问
        },
        "msg": "Video upload and processed successfully！"
    }), 200


if __name__ == '__main__':
    app.run(debug=True ,port=8081)    #设置服务器运行端口为8081
