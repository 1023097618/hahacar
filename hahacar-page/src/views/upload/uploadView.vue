<template>
  <div class="drag-container"
       @dragover.prevent="handleDragOver"
       @dragenter.prevent="handleDragEnter"
       @dragleave.prevent="handleDragLeave"
       @drop.prevent="handleDrop"
       :class="{ 'drag-over': isDragging }">
    <div class="container">
      <h1>在线识别</h1>
      <!-- 上传区域 -->
      <div class="upload-wrapper">
        <div class="upload-text">拖动视频到此识别</div>
        <!-- 自定义按钮，点击后触发隐藏的 file input -->
        <button class="btn-select-file" @click="triggerFileInput">从本设备选择</button>
        <!-- 隐藏的文件输入框 -->
        <input type="file" ref="fileInput" style="display: none" accept="image/*,video/*" @change="handleFileChange" />
        <div class="file-size-tips">
          上传视频/图片
        </div>
      </div>
      <!-- 进度和完成状态区域 -->
      <div class="progress-container" v-if="tasks.length">
        <h2>文件区</h2>
        <div v-for="(task,index) in tasks" :key="index">
          <!-- 正在处理的任务 -->
          <div v-if="!task.isComplete" class="file-progress-item">
            <div class="file-name">{{ task.fileName }}</div>
            <div class="progress-bar-container">
              <div class="progress-bar" :style="{ width: task.progressValue + '%' }"></div>
            </div>
            <div class="progress-percentage">{{ task.progressValue }}% Complete</div>
          </div>
          <!-- 处理完成的任务 -->
          <div v-else class="file-finished-item">
            <div class="file-name">{{ task.fileName }}</div>
            <div class="button-group">
              <button class="btn-view" @click="openLink(task.watchURL)">View</button>
              <button class="btn-download" @click="openLink(task.downloadURL)">Download</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
  import { uploadVideo, uploadPicture } from '@/api/storage/storage.js'
  export default {
    name: 'uploadView',
    data() {
      return {
        isDragging: false,
        dragCounter: 0
      }
    },
    methods: {
      // 触发隐藏的 file input
      triggerFileInput() {
        this.$refs.fileInput.click()
      },
      // 处理文件选择
      handleFileChange(event) {
        const file = event.target.files[0]
        if (!file) return
        this.uploadFile(file)
      },
      // 打开链接
      openLink(url) {
        window.open(url, '_blank')
      },
      // 拖拽相关事件处理
      handleDragOver(event) {
        event.preventDefault()
      },
      handleDragEnter(event) {
        event.preventDefault()
        this.dragCounter++
        if (this.dragCounter === 1) {
          // 只有第一次进入拖拽容器时，设置拖拽状态为 true
          this.isDragging = true
        }
      },
      handleDragLeave(event) {
        event.preventDefault()
        this.dragCounter--
        if (this.dragCounter === 0) {
          // 当所有子元素都离开后重置状态
          this.isDragging = false
        }
      },
      handleDrop(event) {
        event.preventDefault()
        // 重置计数器与拖拽状态
        this.dragCounter = 0
        this.isDragging = false
        if (event.dataTransfer && event.dataTransfer.files && event.dataTransfer.files.length > 0) {
          const file = event.dataTransfer.files[0]
          this.uploadFile(file)
          event.dataTransfer.clearData()
        }
      },
      uploadFile(file) {
        const formData = new FormData()
        formData.append('file', file)
        const fileType = file.type
        let isImage
        if (fileType.startsWith('image/')) {
          isImage = true
        } else if (fileType.startsWith('video/')) {
          isImage = false
        } else {
          return
        }
        const uploadFunction = isImage ? uploadPicture : uploadVideo
        uploadFunction(formData).then(res => {
          if (isImage) {
            this.$store.dispatch("UpdateTasks", {
              type: "picture",
              fileName: file.name,
              ...res.data.data
            })
          }
        }).catch(err => {
          console.log(err)
        })
      }
    },
    computed:{
      tasks(){
        return this.$store.getters.tasks
      }
    }
  }
</script>

<style scoped>
  .drag-container {
    width: 100%;
    height: 100%;
  }
  /* 拖拽反馈样式应用在 drag-container 上 */
  .drag-container.drag-over {
    background-color: #f0f8ff;
  }
  .container {
    max-width: 800px;
    margin: 0 auto;
    padding: 50px 20px;
    text-align: center;
    color: var(--textColor);
  }

  .container h1 {
    font-size: 28px;
    margin-bottom: 20px;
    line-height: 1.4;
  }

  .upload-wrapper {
    background-color: #fff;
    border: 2px dashed #ccc;
    border-radius: 8px;
    padding: 40px 20px;
    margin-top: 30px;
    position: relative;

    background-color: var(--sideBarColor);
    color: var(--textColor);
  }

  .upload-text {
    font-size: 18px;
    margin-bottom: 20px;
  }

  .btn-select-file {
    display: inline-block;
    padding: 12px 24px;
    font-size: 16px;
    color: #fff;
    background-color: #f28705;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    transition: background-color 0.3s ease;
  }

  .btn-select-file:hover {
    background-color: #d87006;
  }

  .file-size-tips {
    margin-top: 20px;
    font-size: 14px;
    color: #999;
    line-height: 1.6;
  }

  /* 进度区域容器 */
  .progress-container {
    margin-top: 40px;
    text-align: left;
  }

  .progress-container h2 {
    font-size: 20px;
    margin-bottom: 20px;
    text-align: center;
  }

  /* 单个文件项 */
  .file-progress-item,
  .file-finished-item {
    background-color: #fff;
    border-radius: 6px;
    padding: 15px;
    margin-bottom: 20px;
    box-shadow: 0 0 8px rgba(0, 0, 0, 0.05);
  }

  .file-name {
    font-size: 16px;
    margin-bottom: 10px;
    color: #333;
    font-weight: bold;
  }

  /* 进度条样式 */
  .progress-bar-container {
    width: 100%;
    height: 12px;
    background-color: #eee;
    border-radius: 6px;
    overflow: hidden;
    position: relative;
    margin-bottom: 10px;
  }

  .progress-bar {
    height: 100%;
    background-color: #4caf50;
    transition: width 0.4s ease;
  }

  .progress-percentage {
    font-size: 14px;
    color: #666;
  }

  /* 完成后显示的按钮 */
  .button-group {
    display: flex;
    gap: 10px;
    justify-content: flex-end;
  }

  .btn-view,
  .btn-download {
    flex: 1;
    padding: 10px;
    font-size: 14px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    transition: background-color 0.3s ease;
  }

  .btn-view {
    background-color: #2196F3;
    color: #fff;
  }

  .btn-view:hover {
    background-color: #1976D2;
  }

  .btn-download {
    background-color: #4CAF50;
    color: #fff;
  }

  .btn-download:hover {
    background-color: #388E3C;
  }
</style>
