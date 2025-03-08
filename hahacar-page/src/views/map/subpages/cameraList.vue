<template>
    <div class="camera-page">
      <!-- 顶部 Header -->
      <div class="camera-header">
        <div class="back-arrow" @click="goBack">
          <i class="fa fa-arrow-left"></i>
        </div>
        <div class="header-title">摄像头列表</div>
      </div>
  
      <!-- 摄像头列表 -->
      <div class="camera-grid">
        <div class="camera-item" v-for="camera in cameras" :key="camera.cameraId">
          <!-- HTTP JPEG STREAM 的摄像头画面 -->
          <img :src="getCameraLiveStream+'?token='+token +'&type=preview&cameraId='+camera.cameraId" :alt="camera.cameraName" class="camera-feed" @click.stop.prevent="OpenDetail(camera)"/>
          <div class="camera-name">{{ camera.cameraName }}</div>
        </div>
      </div>
  
      <!-- 分页 -->
      <div class="pagination">
        <button @click="prevPage" :disabled="pageNum === 1">上一页</button>
        <span
          v-for="page in totalPages"
          :key="page"
          class="page-number"
          :class="{ active: page === pageNum }"
          @click="changePage(page)"
        >
          {{ page }}
        </span>
        <button @click="nextPage" :disabled="pageNum === totalPages">下一页</button>
      </div>
    </div>
  </template>
  
  <script>
    import {getCameraList} from '@/api/camera/camera.js'
    import {getCameraLiveStream} from '@/api/storage/storage.js'
  export default {
    name: 'CameraPage',
    data() {
      return {
        // 示例摄像头数据，请替换为实际接口返回数据
        cameras: [
          // { cameraId: 1, cameraName: '摄像头 1', cameraLiveStreamPreviewURL: 'http://example.com/stream1.jpg' },
          // { cameraId: 2, cameraName: '摄像头 2', cameraLiveStreamPreviewURL: 'http://example.com/stream2.jpg' },
          // { cameraId: 3, cameraName: '摄像头 3', cameraLiveStreamPreviewURL: 'http://example.com/stream3.jpg' },
          // { cameraId: 4, cameraName: '摄像头 4', cameraLiveStreamPreviewURL: 'http://example.com/stream4.jpg' },
          // { cameraId: 5, cameraName: '摄像头 5', cameraLiveStreamPreviewURL: 'http://example.com/stream5.jpg' },
          // { cameraId: 6, cameraName: '摄像头 6', cameraLiveStreamPreviewURL: 'http://example.com/stream6.jpg' },
          // { cameraId: 7, cameraName: '摄像头 7', cameraLiveStreamPreviewURL: 'http://example.com/stream7.jpg' },
          // { cameraId: 8, cameraName: '摄像头 8', cameraLiveStreamPreviewURL: 'http://example.com/stream8.jpg' },
          // 根据需求增加更多摄像头
        ],
        pageNum: 1,
        pageSize: 6,
        cameraNum:8,
        getCameraLiveStream
      };
    },
    computed: {
      totalPages() {
        return Math.ceil(this.cameraNum / this.pageSize);
      },
      token(){
        return this.$store.getters.token
      }
    },
    methods: {
      goBack() {
        // 返回上个页面
        this.$router.go(-1);
      },
      changePage(page) {
        this.pageNum = page;
        this.GetCameraList()
      },
      prevPage() {
        if (this.pageNum > 1) {
          this.pageNum--;
        }
        this.GetCameraList()
      },
      nextPage() {
        if (this.pageNum < this.totalPages) {
          this.pageNum++;                                                                                        
        }
        this.GetCameraList()
      },
      GetCameraList(){
        getCameraList({
            pageNum:this.pageNum,
            pageSize:this.pageSize
        }).then(res=>{
            this.cameras=res.data.data.cameras
            this.cameraNum=res.data.data.cameraNum
        }).catch(err=>{
            console.log(err)
        })
      },
      OpenDetail(camera){
        window.open(getCameraLiveStream+'?token='+this.token +'&type=full&cameraId='+camera.cameraId,"_blank")
      }
    },
    created(){
      this.GetCameraList()
    }
  };
  </script>
  
  <style scoped>
  .camera-page {
    display: flex;
    flex-direction: column;
    height: 100vh;
    background: #f5f5f5;
  }
  
  /* Header 样式 */
  .camera-header {
    height: 50px;
    background-color: #081737;
    color: #fff;
    display: flex;
    align-items: center;
    padding: 0 20px;
  }
  
  .back-arrow {
    cursor: pointer;
    margin-right: 10px;
  }
  
  .back-arrow i {
    font-size: 18px;
  }
  
  .header-title {
    font-size: 18px;
    font-weight: bold;
  }
  
  /* 摄像头列表网格 */
  .camera-grid {
    flex: 1;
    display: flex;
    flex-wrap: wrap;
    padding: 20px;
    gap: 20px;
    overflow-y: auto;
  }
  
  .camera-item {
    background: #fff;
    border: 1px solid #ddd;
    border-radius: 4px;
    width: calc(33.33% - 20px); /* 每行 3 个 */
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    display: flex;
    flex-direction: column;
    align-items: center;
  }
  
  .camera-feed {
    width: 100%;
    /* 如果需要固定画面尺寸，可以设置 height: 200px; object-fit: cover; */
  }
  
  .camera-name {
    padding: 10px;
    font-size: 14px;
    text-align: center;
  }
  
  /* 分页样式 */
  .pagination {
    height: 50px;
    background: #fff;
    display: flex;
    align-items: center;
    justify-content: center;
    border-top: 1px solid #ddd;
  }
  
  .pagination button {
    margin: 0 10px;
    padding: 5px 10px;
    cursor: pointer;
  }
  
  .page-number {
    margin: 0 5px;
    cursor: pointer;
    padding: 5px 10px;
    border-radius: 3px;
  }
  
  .page-number.active {
    background-color: #081737;
    color: #fff;
  }
  </style>
  