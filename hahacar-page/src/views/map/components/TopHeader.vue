<template>
    <div class="top-header">
      <!-- 左侧：平台名称 -->
      <div class="left">
        <div class="platform-name">城市公共安全智慧平台</div>
      </div>
  
      <!-- 右侧：固定 6 个统计项 -->
      <div class="right">

        <!-- <div class="info-item">
          <i class="fa fa-exclamation-triangle"></i>
          <span class="info-label">警情总数</span>
          <span class="info-value">1009</span>
        </div>
  

        <div class="info-item">
          <i class="fa fa-user"></i>
          <span class="info-label">在线人数</span>
          <span class="info-value">331</span>
        </div>
  

        <div class="info-item">
          <i class="fa fa-bell"></i>
          <span class="info-label">报警数</span>
          <span class="info-value">28</span>
        </div> -->
  

        <div class="info-item clickable" @click="goCameraPage">
          <i class="fa fa-video"></i>
          <span class="info-label">摄像头</span>
          <span class="info-value">{{cameras.cameraNum}}</span>
        </div>
  

        <!-- <div class="info-item">
          <i class="fa fa-user-shield"></i>
          <span class="info-label">重点人员</span>
          <span class="info-value">103</span>
        </div>
  

        <div class="info-item">
          <i class="fa fa-car"></i>
          <span class="info-label">重点车辆</span>
          <span class="info-value">6</span>
        </div> -->
      </div>
    </div>
  </template>
  
  <script>
  export default {
    name: 'TopHeader',
    methods: {
      // 点击后跳转到 /camera
      goCameraPage() {
        this.$router.push('/cameraList')
      }
    },
    // props:["cameras"]
    props:{
        cameras:{
            required:true,
            type:Object
        }
    }
  }
  </script>
  
  <style scoped>
  .top-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 70px;
    background-color: #081737;
    padding: 0 20px;
    color: #fff;
  }
  
  .left .platform-name {
    font-size: 20px;
    font-weight: bold;
  }
  
  .right {
    display: flex;
    align-items: center;
  }
  
  .info-item {
    width: 90px;
    margin-left: 25px;
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
  }
  
  /* 让鼠标悬浮时出现指针手势 */
  .info-item.clickable {
    cursor: pointer;
  }

  .info-item.clickable:hover{
    background-color: rgba(255, 255, 255, 0.2); /* 悬浮时背景变亮 */
    border-radius: 5px; /* 可选：增加圆角效果 */
  }
  
  .info-item i {
    font-size: 16px;
    margin-bottom: 3px;
  }
  
  .info-label {
    font-size: 12px;
    opacity: 0.8;
  }
  .info-value {
    font-size: 14px;
    font-weight: bold;
  }
  </style>
  