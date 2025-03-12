<template>
  <div style="height: 100%;">
    <!-- 顶部 -->
    <top-header :cameras="cameras" :alerts="alerts"/>

    <!-- 地图区域 -->
    <map-container :cameras="cameras"/>
  </div>
</template>

<script>
import {getCameraList} from '@/api/camera/camera.js'
import { getAlerts } from '@/api/alert/alert.js'
import TopHeader from './components/TopHeader.vue';
import MapContainer from './components/MapContainer.vue';
//获取到所有的摄像头，因为要全部显示到地图上
const max_number=10000
export default {
  name: 'App',
  components: {
    TopHeader,
    MapContainer
  },
  created(){
    getCameraList({
      pageNum:1,
      pageSize:max_number
    }).then(res=>{
      this.cameras=res.data.data
    }).catch(err=>{
      console.log(err)
    }),
    getAlerts({
      pageNum:1,
      pageSize:0,
      alertType:["1","2"]
    }).then(res=>{
      this.alerts=res.data.data
    }).catch(err=>{
      console.log(err)
    })
  },
  data(){
    return {
      cameras:{},
      alerts:{}
    }
  }
};
</script>

<style scoped>
/* 基础样式重置 */
html, body, #app {
  margin: 0;
  padding: 0;
  height: 100%;
  background: #0f1c3c; /* 整体背景深色 */
  font-family: "Microsoft YaHei", sans-serif;
}
</style>
