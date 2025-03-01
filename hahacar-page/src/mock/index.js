const Mock=require('mockjs')
const baseurl = process.env.VUE_APP_baseurl

Mock.mock(baseurl+"/auth/login", 'post', require('./json/login/login.json'));
Mock.mock(baseurl+"/auth/info?token=123", 'get', require('./json/login/info.json'));