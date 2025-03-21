<template>
  <div class="camera-map-page">
    <el-row :gutter="20">
      <!-- 左侧：摄像头画面及绘图区域 -->
      <el-col :span="12">
        <div class="camera-section" ref="cameraContainer">
          <!-- 摄像头实时画面 -->
          <img :src="GetCameraLiveURL(cameraId)" alt="Camera Live" class="camera-image" @load="onImageLoad" />
          <!-- Canvas 绘图层，覆盖在图片上 -->
          <canvas ref="drawingCanvas" class="drawing-canvas" @mousedown="handleMouseDown" @mousemove="handleMouseMove"
            @mouseup="handleMouseUp"></canvas>
        </div>
      </el-col>

      <!-- 右侧：地图 -->
      <el-col :span="12">
        <div class="map-section" ref="mapContainer"></div>
      </el-col>
    </el-row>

    <!-- 编辑表单区域 -->
    <el-card class="line-form-panel" style="margin-top: 20px;">
      <div v-for="(line, index) in lines" :key="line.cameraLineId" class="line-form">
        <el-form :model="line" label-width="120px" inline>
          <el-form-item label="检测线名称">
            <el-input v-model="line.cameraLineName" placeholder="请输入检测线名称"></el-input>
          </el-form-item>
          <el-form-item label="坐标信息">
            <el-input :value="formatLinePoints(line.points)" disabled></el-input>
          </el-form-item>
          <el-form-item label="关联地图点">
            <el-input :value="formatAssociatedPoint(line.pointCloseToLine)" disabled></el-input>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" size="small" @click="setLineAssociation(index)">
              关联地图点
            </el-button>
          </el-form-item>
          <!-- 新增主要检测线勾选 -->
          <el-form-item label="主要检测线">
            <el-checkbox v-model="line.isMainLine" @change="onMainLineChange(index)">
              是
            </el-checkbox>
          </el-form-item>
          <el-form-item>
            <el-button type="danger" size="small" @click="deleteLine(index)">
              删除
            </el-button>
          </el-form-item>
        </el-form>
      </div>
    </el-card>

    <!-- 底部保存按钮 -->
    <el-row style="margin-top: 20px">
      <el-col :span="24" class="text-center">
        <el-button type="primary" @click="saveLines">
          <i class="el-icon-upload"></i> 保存检测线
        </el-button>
      </el-col>
    </el-row>
  </div>
</template>

<script>
  // 引入接口方法、地图加载脚本
  import { getCameraLiveURL } from '@/api/storage/storage.js'
  import { getCameraLines, updateCameraLine } from '@/api/camera/cameraLines'
  import { loadAMap } from '@/utils/loadAMap.js'

  // 使用 require 加载 marker 图标资源
  const defaultIconUrl = require('@/assets/default_marker.png')

  export default {
    name: 'CameraLines',
    data() {
      return {
        cameraId: -1,
        // 检测线数组，每条线包含：名称、坐标、关联地图点、ID、marker，以及 isMainLine（是否为主要检测线）
        lines: [],
        // 当前正在绘制的线条数据
        currentLine: { points: [] },
        isDrawing: false,
        canvasWidth: 640,
        canvasHeight: 480,
        ctx: null,
        selectedLineIndex: null,
        map: null,
        defaultIconUrl: defaultIconUrl
      }
    },
    created() {
      this.cameraId = this.$route.query.cameraId
      this.fetchCameraLines()
    },
    mounted() {
      this.initCanvas()
      this.initMap()
    },
    methods: {
      // 获取摄像头实时画面 URL
      GetCameraLiveURL(cameraId) {
        return getCameraLiveURL(cameraId)
      },
      onImageLoad(e) {
        const img = e.target
        this.canvasWidth = img.clientWidth
        this.canvasHeight = img.clientHeight
        const canvas = this.$refs.drawingCanvas
        canvas.width = this.canvasWidth
        canvas.height = this.canvasHeight
        this.redrawCanvas()
      },
      initCanvas() {
        const canvas = this.$refs.drawingCanvas
        this.ctx = canvas.getContext('2d')
      },
      redrawCanvas() {
        if (!this.ctx) return
        this.ctx.clearRect(0, 0, this.canvasWidth, this.canvasHeight)
        // 绘制所有已完成的线条（蓝色）
        this.lines.forEach(line => {
          const pts = line.points
          this.ctx.beginPath()
          this.ctx.moveTo(pts[0], pts[1])
          this.ctx.lineTo(pts[2], pts[3])
          this.ctx.strokeStyle = 'blue'
          this.ctx.lineWidth = 2
          this.ctx.lineCap = 'round'
          this.ctx.stroke()
        })
        // 绘制正在绘制的预览线（红色）
        if (this.isDrawing && this.currentLine.points.length === 4) {
          const pts = this.currentLine.points
          this.ctx.beginPath()
          this.ctx.moveTo(pts[0], pts[1])
          this.ctx.lineTo(pts[2], pts[3])
          this.ctx.strokeStyle = 'red'
          this.ctx.lineWidth = 2
          this.ctx.lineCap = 'round'
          this.ctx.stroke()
        }
      },
      handleMouseDown(e) {
        const rect = this.$refs.drawingCanvas.getBoundingClientRect()
        const x = e.clientX - rect.left
        const y = e.clientY - rect.top
        this.isDrawing = true
        this.currentLine.points = [x, y]
      },
      handleMouseMove(e) {
        if (!this.isDrawing) return
        const rect = this.$refs.drawingCanvas.getBoundingClientRect()
        const x = e.clientX - rect.left
        const y = e.clientY - rect.top
        if (this.currentLine.points.length === 1) {
          this.currentLine.points.push(x, y)
        } else {
          this.currentLine.points[2] = x
          this.currentLine.points[3] = y
        }
        this.redrawCanvas()
      },
      handleMouseUp() {
        if (!this.isDrawing) return
        this.isDrawing = false
        if (this.currentLine.points.length === 4) {
          // 新增的检测线默认 isMainLine 为 false
          this.lines.push({
            cameraLineName: '检测线',
            points: [...this.currentLine.points],
            pointCloseToLine: [],
            cameraLineId: Date.now().toString(),
            marker: null,
            isMainLine: false
          })
        }
        this.currentLine.points = []
        this.redrawCanvas()
      },
      fetchCameraLines() {
        getCameraLines({ cameraId: this.cameraId })
          .then(response => {
            const linesData = response.data.data.cameraLines || []
            this.lines = linesData.map(item => {
              return {
                cameraLineName: item.cameraLineName || '检测线',
                points: [
                  parseFloat(item.cameraLineStartX) * this.canvasWidth,
                  parseFloat(item.cameraLineStartY) * this.canvasHeight,
                  parseFloat(item.cameraLineEndX) * this.canvasWidth,
                  parseFloat(item.cameraLineEndY) * this.canvasHeight
                ],
                // 后端传来的关联点为字符串数组
                pointCloseToLine: item.pointCloseToLine || [],
                cameraLineId: item.cameraLineId,
                marker: null,
                // 转换 isMainLine 字段（支持 boolean 或字符串形式）
                isMainLine: item.isMainLine === true || item.isMainLine === 'true'
              }
            })
            this.redrawCanvas()
            // 如果地图已初始化，则创建 marker 并更新中心点
            if (this.map) {
              this.drawMarkers()
              this.updateMapCenter()
            }
          })
          .catch(err => {
            console.error('获取摄像头检测线失败:', err)
          })
      },
      // 为所有存在关联点且未创建 marker 的检测线创建 marker
      drawMarkers() {
        this.lines.forEach(line => {
          if (
            line.pointCloseToLine &&
            line.pointCloseToLine.length === 2 &&
            !line.marker
          ) {
            const lng = parseFloat(line.pointCloseToLine[0])
            const lat = parseFloat(line.pointCloseToLine[1])
            const marker = new window.AMap.Marker({
              position: [lng, lat],
              title: line.cameraLineName,
              icon: this.defaultIconUrl,
              offset: new window.AMap.Pixel(-26, -60)
            })
            marker.setMap(this.map)
            line.marker = marker
          }
        })
      },
      setLineAssociation(index) {
        this.selectedLineIndex = index
        this.$message.info(`请在地图上点击选择关联点，当前选择：${this.lines[index].cameraLineName}`)
      },
      deleteLine(index) {
        if (this.selectedLineIndex === index) {
          this.selectedLineIndex = null
        }
        if (this.lines[index].marker) {
          this.lines[index].marker.setMap(null)
        }
        this.lines.splice(index, 1)
        this.redrawCanvas()
        this.updateMapCenter()
      },
      formatLinePoints(points) {
        if (!points || points.length !== 4) return ''
        return `${(points[0] / this.canvasWidth).toFixed(3)},${(points[1] / this.canvasHeight).toFixed(3)} -> ${(points[2] / this.canvasWidth).toFixed(3)},${(points[3] / this.canvasHeight).toFixed(3)}`
      },
      formatAssociatedPoint(point) {
        return point && point.length === 2
          ? `${parseFloat(point[0]).toFixed(2)}, ${parseFloat(point[1]).toFixed(2)}`
          : '未关联'
      },
      // 当勾选主要检测线时，确保只有一条为 true
      onMainLineChange(index) {
        // 当当前检测线被选中后，其他均置为 false
        this.lines.forEach((line, i) => {
          line.isMainLine = (i === index)
        })
      },
      initMap() {
        loadAMap()
          .then(AMap => {
            // 初始中心点，后续会根据关联点更新
            this.map = new AMap.Map(this.$refs.mapContainer, {
              zoom: 12,
              center: [116.397428, 39.90923]
            })
            // 地图点击事件：如果有待关联的检测线，则更新关联点并添加 marker
            this.map.on('click', (e) => {
              if (this.selectedLineIndex !== null) {
                const lng = e.lnglat.getLng()
                const lat = e.lnglat.getLat()
                const currentLine = this.lines[this.selectedLineIndex]
                currentLine.pointCloseToLine = [lng, lat]
                if (currentLine.marker) {
                  currentLine.marker.setMap(null)
                }
                const marker = new window.AMap.Marker({
                  position: [lng, lat],
                  title: currentLine.cameraLineName,
                  icon: this.defaultIconUrl,
                  offset: new window.AMap.Pixel(-26, -60)
                })
                marker.setMap(this.map)
                currentLine.marker = marker
                this.$message.success(`已关联地图点：${lng.toFixed(2)}, ${lat.toFixed(2)}`)
                this.selectedLineIndex = null
                this.updateMapCenter()
              }
            })
            // 地图初始化后，为已加载检测线添加 marker（如果有关联点）
            this.drawMarkers()
            this.updateMapCenter()
          })
          .catch(err => {
            console.error('加载高德地图失败:', err)
          })
      },
      // 根据所有检测线关联点的平均值更新地图中心
      updateMapCenter() {
        if (!this.map) return
        let sumLng = 0, sumLat = 0, count = 0
        this.lines.forEach(line => {
          if (line.pointCloseToLine && line.pointCloseToLine.length === 2) {
            sumLng += parseFloat(line.pointCloseToLine[0])
            sumLat += parseFloat(line.pointCloseToLine[1])
            count++
          }
        })
        if (count > 0) {
          const center = [sumLng / count, sumLat / count]
          this.map.setCenter(center)
        }
      },
      saveLines() {
        const payload = {
          cameraLines: this.lines.map(line => {
            const pts = line.points
            return {
              cameraLineName: line.cameraLineName,
              cameraLineStartX: (pts[0] / this.canvasWidth).toString(),
              cameraLineStartY: (pts[1] / this.canvasHeight).toString(),
              cameraLineEndX: (pts[2] / this.canvasWidth).toString(),
              cameraLineEndY: (pts[3] / this.canvasHeight).toString(),
              pointCloseToLine: line.pointCloseToLine ? line.pointCloseToLine.map(coord => coord.toString()) : [],
              isMainLine: line.isMainLine ? 'true' : 'false',
              cameraLineId: line.cameraLineId
            }
          }),
          cameraId: this.cameraId
        }
        updateCameraLine(payload)
          .then(() => {
            this.$message.success('保存成功')
          })
          .catch(err => {
            console.log('payload', JSON.stringify(payload, null, 2))
            console.error('保存摄像头检测线失败:', err)
            this.$message.error('保存失败')
          })
      }
    }
  }
</script>

<style scoped>
  .camera-map-page {
    padding: 20px;
  }

  .camera-section {
    position: relative;
    width: 640px;
    height: 480px;
  }

  .camera-image {
    width: 100%;
    height: 100%;
    display: block;
  }

  .drawing-canvas {
    position: absolute;
    top: 0;
    left: 0;
    z-index: 10;
    pointer-events: all;
  }

  .map-section {
    width: 100%;
    height: 480px;
    border: 1px solid #dcdfe6;
  }

  .line-form-panel {
    margin-top: 20px;
  }

  .line-form {
    margin-bottom: 10px;
  }
</style>