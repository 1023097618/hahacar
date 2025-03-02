<!-- <template>
    <video ref="videoPlayer" controls autoplay></video>
  </template>
  
  <script>
  import Hls from "hls.js";
  
  export default {
    mounted() {
      this.playStream();
    },
    methods: {
      playStream() {
        const video = this.$refs.videoPlayer;
        const hls = new Hls();
        hls.loadSource("http://localhost:5000/video/stream.m3u8");
        hls.attachMedia(video);
      },
    },
  };
  </script> -->

  
  <template>
    <div id="app">
      <!-- 使用后端推流地址，注意跨域问题，如需可配置 CORS -->
      <img :src="videoSrc" alt="视频流" />
    </div>
  </template>
  
  <script>
  export default {
    name: "App",
    data() {
      return {
        // 根据实际情况修改地址，默认后端运行在 localhost:5000
        videoSrc: "http://localhost:5000/video_feed"
      };
    }
  };
  </script>
  
  <style>
  /* 可根据需要添加样式 */
  #app {
    text-align: center;
    margin-top: 20px;
  }
  </style>
  