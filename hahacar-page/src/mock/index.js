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

Mock.mock(baseurl+"/label/getLabels",'get',require('./json/label/label.json'))
Mock.mock(baseurl+"/camera/getCameraRules?cameraId=1",'get',require('./json/camera/cameraRule.json'))
Mock.mock(baseurl+"/camera/getCameraLines?cameraId=1",'get',require('./json/camera/cameraLine.json'))

Mock.mock(baseurl+"/stat/alert/searchAlertNum",'get',require('./json/stat/alert/alert.json'))
Mock.mock(baseurl+"/stat/category/searchCategoryNum",'get',require('./json/stat/category/category.json'))
Mock.mock(baseurl+"/stat/flow/searchFlowNum",'get',require('./json/stat/flow/flow.json'))
Mock.mock(baseurl+"/stat/hold/searchHoldNum",'get',require('./json/stat/hold/hold.json'))
Mock.mock(baseurl+"/stat/flow/getFlowMat?cameraId=1",'get',require('./json/stat/flow/getFlowMat.json'))

Mock.mock(baseurl+"/alert/getAlerts?pageNum=1&pageSize=0&alertType[]=1&alertType[]=2",'get',require('./json/alert/alert.json'))
Mock.mock(baseurl+"/alert/getAlerts?pageNum=1&pageSize=20",'get',require('./json/alert/alert.json'))
Mock.mock(baseurl+"/alert/getAlerts?pageNum=1&pageSize=20&alertType[]=1&alertType[]=2",'get',require('./json/alert/alert.json'))

Mock.mock(baseurl+"/event/getEvents",'get',require('./json/event/event.json'))