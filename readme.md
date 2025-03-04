目录介绍:

1. `hahacar-page`为项目前端页面，使用如下方式运行
``` cmd
cd hahacar-page
npm i
npm run serve
```

2. `hahacar-serve`为项目后端，使用如下方式运行[已测试]

[python](https://www.python.org/downloads/release/python-3117/)版本为`3.11.7`，使用以下命令对后端进行启动
``` cmd
python -m venv hahacar
${path_to_your_hahacar_environment}\Scripts\activate
cd hahacar_server
pip install -r require.txt
uvicorn main:app --host 0.0.0.0 --port 8081 --reload
```

[此处后面会调整，暂时不调用模型]

由于需要调用模型，需要先将yolo模型本地部署，否则无法运行

- 本地部署[yolo模型](https://github.com/dyh/unbox_yolov5_deepsort_counting?tab=readme-ov-file)

- 把`hahacar-serve`目录下所有文件\文件夹放入模型`unbox_yolov5_deepsort_counting\`下

- 启动后端服务
  ```bash
  python input_video_prosess_api.py
  ```


3. 该项目的接口地址位于[此处](https://app.apifox.com/project/5927090)

4. `dev`文件是一个空文件，您可以放置在开发过程中产生的想法、参考的资料等等，它不会被上传到github



  
   



