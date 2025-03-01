目录介绍:

1. `hahacar-page`为项目前端页面，使用如下方式运行
``` cmd
cd hahacar-page
npm i
npm run serve
```

2. `hahacar-serve`为项目后端服务器


3. 该项目的接口地址位于此处`https://app.apifox.com/project/5927090`

4. `dev`文件是一个空文件，您可以放置在开发过程中产生的想法、参考的资料等等，它不会被上传到github

5. yuxin-backend为项目后端
由于需要调用模型，需要先将yolo模型本地部署，否则无法运行
- 本地部署yolo模型https://github.com/dyh/unbox_yolov5_deepsort_counting?tab=readme-ov-file

- 把yuxin-backend目录下所有文件\文件夹放入模型unbox_yolov5_deepsort_counting\下

- 安装依赖

  ```bash
  pip install -r requirements.txt  # 安装依赖
  ```

- 启动后端服务

  ```bash
  python input_video_prosess_api.py
  ```

  
   



