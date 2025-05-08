目录介绍:

1. `hahacar-page`为项目前端页面，使用如下方式运行
``` cmd
cd hahacar-page
npm i
npm run serve
```

使用如下方式进行打包
``` cmd
npm run build
```

2. `hahacar-serve`为项目后端，使用如下方式运行[已测试]

首先下载模型文件，放至util/weights 文件夹下，模型文件下载地址将在接下来给出

[python](https://www.python.org/downloads/release/python-3117/)版本为`3.11.7`，使用以下命令对后端进行启动
``` cmd
python -m venv hahacar
${path_to_your_hahacar_environment}\Scripts\activate
cd hahacar_server
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8081
```


3. 该项目的接口地址位于[此处](https://apifox.com/apidoc/shared-4d9bbf09-7f74-4266-9663-eef4bc1aceb6)

4. `dev`文件是一个空文件，您可以放置在开发过程中产生的想法、参考的资料等等，它不会被上传到github



  
   



