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

  
  <!-- <template>
    <div id="app">
      <img :src="videoSrc" alt="视频流" />
    </div>
  </template>
  
  <script>
  export default {
    name: "App",
    data() {
      return {
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
  </style> -->
  

  <!-- <template>
    <div>
      <button @click="sendCustomEvent">Send Custom Event</button>
    </div>
  </template>
  
  <script>
  import { io } from "socket.io-client";
  
  export default {
    data() {
      return {
        socket: null,
      };
    },
    mounted() {
      this.socket = io("http://localhost:5000");
  
      // 监听后端的 response_event 事件
      this.socket.on("response_event", (data) => {
        console.log("Received from server:", data);
      });
    },
    methods: {
      sendCustomEvent() {
        this.socket.emit("custom_event", { username: "Alice", message: "Hello Server!" });
      },
    },
    beforeUnmount() {
      if (this.socket) {
        this.socket.disconnect();
      }
    },
  };
  </script>
   -->
   <template>
    <div id="app">
      <h1>视频流展示</h1>
      <!-- src 中带上 token 参数 -->
      <img :src="videoSrc" alt="视频流" />
    </div>
  </template>
  
  <script>
  export default {
    name: 'VideoStream',
    data() {
      return {
        // 在实际项目中，token 可以从登录状态或配置中获取
        token: 'expected_token',
        videoSrc: ''
      }
    },
    mounted() {
      // 构造包含 token 参数的视频流 URL
      this.videoSrc = `http://localhost:5000/proxy_video_feed?token=${this.token}`
    }
  }
  </script>
  
  <style scoped>
  #app {
    text-align: center;
    margin-top: 20px;
  }
  
  img {
    max-width: 100%;
    border: 1px solid #ccc;
  }
  </style>
  
  