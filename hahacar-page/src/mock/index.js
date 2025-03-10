const Mock=require('mockjs')
const baseurl = process.env.VUE_APP_baseurl

Mock.mock(baseurl+"/auth/login", 'post', require('./json/login/login.json'));
Mock.mock(baseurl+"/auth/info?token=123", 'get', require('./json/login/info.json'));
Mock.mock(baseurl+"/user/styleChange", 'post', require('./json/success.json'));
Mock.mock(baseurl+"/camera/getCameras?pageNum=1&pageSize=10000",'get',require('./json/camera/cameraList.json'))
Mock.mock(baseurl+"/camera/getCameras?pageNum=1&pageSize=6",'get',require('./json/camera/cameraList.json'))
Mock.mock(baseurl+"/camera/getCameras?pageNum=1&pageSize=20",'get',require('./json/camera/cameraList.json'))
Mock.mock(baseurl+"/user/getUsers?pageNum=1&pageSize=10",'get',require('./json/user/userList.json'))
Mock.mock(baseurl+"/user/getUserCameraPrivilege?userId=123",'get',require('./json/user/getUserCameraPrivilege.json'))

