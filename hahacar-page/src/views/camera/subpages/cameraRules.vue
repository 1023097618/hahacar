<template>
  <div class="rules-container">
    <h2>摄像头规则配置 - 摄像头ID：{{ cameraId }}</h2>
    <!-- 添加规则按钮 -->
    <el-button type="primary" @click="addRule" style="margin-bottom: 20px;">添加规则</el-button>

    <!-- 规则列表 -->
    <div v-for="(rule, index) in rules" :key="index" class="rule-card">
      <el-card shadow="hover" style="margin-bottom: 20px;">
        <div slot="header" class="clearfix">
          <el-button type="text" @click="removeRule(index)">删除</el-button>
          <span>规则 {{ index + 1 }}</span>
        </div>
        <el-form :model="rule" label-width="120px">
          <el-form-item label="规则类型">
            <el-select v-model="rule.ruleValue" placeholder="请选择规则类型" style="width: 200px;"
              @change="handleRuleTypeChange(rule)">
              <el-option label="车辆类别预警" value="1"></el-option>
              <el-option label="车辆拥堵预警" value="2"></el-option>
              <el-option label="车流量预警" value="3"></el-option>
              <el-option label="车辆预约检测" value="4"></el-option>
              <el-option label="异常事故预警" value="5"></el-option>
            </el-select>
          </el-form-item>

          <!-- 当规则类型为1：车辆类别预警时 -->
          <div v-if="rule.ruleValue === '1'">
            <el-form-item label="选择标签">
              <el-select v-model="rule.label.labelId" multiple placeholder="请选择标签" style="width: 300px;">
                <el-option v-for="item in labels" :key="item.labelId" :label="item.labelName"
                  :value="item.labelId"></el-option>
              </el-select>
            </el-form-item>
            <el-form-item label="选择检测线" @mouseenter.native="handleDetectionLineHover(rule.label.cameraLineId)"
              @mouseleave.native="clearLineHighlight">
              <el-select v-model="rule.label.cameraLineId" placeholder="请选择检测线" style="width: 300px;">
                <el-option v-for="line in cameraLines" :key="line.cameraLineId" :label="line.cameraLineName"
                  :value="line.cameraLineId"></el-option>
              </el-select>
            </el-form-item>
          </div>

          <!-- 当规则类型为2：车辆拥堵预警时 -->
          <div v-if="rule.ruleValue === '2'">
            <el-form-item label="最大交通当量">
              <el-input v-model="rule.VehicleHold.maxVehicleHoldNum" placeholder="例如：1.5"
                style="width:200px;"></el-input>
            </el-form-item>
            <el-form-item label="最大持续时长">
              <el-input-number v-model="rule.VehicleHold.maxContinuousTimePeriod" :min="0"></el-input-number>
            </el-form-item>
            <el-form-item label="最小交通当量">
              <el-input v-model="rule.VehicleHold.minVehicleHoldNum" placeholder="例如：1.0"
                style="width:200px;"></el-input>
            </el-form-item>
            <el-form-item label="最小持续时长">
              <el-input-number v-model="rule.VehicleHold.minContinuousTimePeriod" :min="0"></el-input-number>
            </el-form-item>
            <el-form-item label="交通当量设置">
              <div v-for="(item, i) in rule.VehicleHold.LabelsEqual" :key="i" class="labels-equal-item">
                <el-select v-model="item.labelId" placeholder="选择标签" style="width:150px;">
                  <el-option v-for="label in labels" :key="label.labelId" :label="label.labelName"
                    :value="label.labelId"></el-option>
                </el-select>
                <el-input v-model="item.labelHoldNum" placeholder="当量"
                  style="width:100px; margin-left:10px;"></el-input>
                <el-button type="text" @click="removeLabelsEqual(rule.VehicleHold.LabelsEqual, i)">删除</el-button>
              </div>
              <el-button type="primary" @click="addLabelsEqual(rule, 'VehicleHold')">添加当量设置</el-button>
            </el-form-item>
          </div>

          <!-- 当规则类型为3：车流量预警时 -->
          <div v-if="rule.ruleValue === '3'">
            <el-form-item label="最大交通当量">
              <el-input v-model="rule.VehicleFlow.maxVehicleFlowNum" placeholder="例如：1.5"
                style="width:200px;"></el-input>
            </el-form-item>
            <el-form-item label="最大持续时长">
              <el-input-number v-model="rule.VehicleFlow.maxContinuousTimePeriod" :min="0"></el-input-number>
            </el-form-item>
            <el-form-item label="最小交通当量">
              <el-input v-model="rule.VehicleFlow.minVehicleFlowNum" placeholder="例如：1.0"
                style="width:200px;"></el-input>
            </el-form-item>
            <el-form-item label="最小持续时长">
              <el-input-number v-model="rule.VehicleFlow.minContinuousTimePeriod" :min="0"></el-input-number>
            </el-form-item>
            <el-form-item label="交通当量设置">
              <div v-for="(item, i) in rule.VehicleFlow.LabelsEqual" :key="i" class="labels-equal-item">
                <el-select v-model="item.labelId" placeholder="选择标签" style="width:150px;">
                  <el-option v-for="label in labels" :key="label.labelId" :label="label.labelName"
                    :value="label.labelId"></el-option>
                </el-select>
                <el-input v-model="item.labelEqualNum" placeholder="当量"
                  style="width:100px; margin-left:10px;"></el-input>
                <el-button type="text" @click="removeLabelsEqual(rule.VehicleFlow.LabelsEqual, i)">删除</el-button>
              </div>
              <el-button type="primary" @click="addLabelsEqual(rule, 'VehicleFlow')">添加当量设置</el-button>
            </el-form-item>
            <el-form-item label="摄像头起始线"
              @mouseenter.native="handleDetectionLineHover(rule.VehicleFlow.cameraStartLine.cameraLineId)"
              @mouseleave.native="clearLineHighlight">
              <el-select v-model="rule.VehicleFlow.cameraStartLine.cameraLineId" placeholder="选择起始检测线"
                style="width:200px;">
                <el-option v-for="line in cameraLines" :key="line.cameraLineId" :label="line.cameraLineName"
                  :value="line.cameraLineId"></el-option>
              </el-select>
              <el-checkbox v-model="rule.VehicleFlow.cameraStartLine.isAll" style="margin-left:10px;">全部</el-checkbox>
            </el-form-item>
            <el-form-item label="摄像头终止线"
              @mouseenter.native="handleDetectionLineHover(rule.VehicleFlow.cameraEndLine.cameraLineId)"
              @mouseleave.native="clearLineHighlight">
              <el-select v-model="rule.VehicleFlow.cameraEndLine.cameraLineId" placeholder="选择终止检测线"
                style="width:200px;">
                <el-option v-for="line in cameraLines" :key="line.cameraLineId" :label="line.cameraLineName"
                  :value="line.cameraLineId"></el-option>
              </el-select>
              <el-checkbox v-model="rule.VehicleFlow.cameraEndLine.isAll" style="margin-left:10px;">全部</el-checkbox>
            </el-form-item>
          </div>

          <!-- 当规则类型为4：车辆预约检测时 -->
          <div v-if="rule.ruleValue === '4'">
            <el-form-item label="预约车辆检测">
              <el-checkbox v-model="rule.VehicleReserve">开启预约车辆检测</el-checkbox>
            </el-form-item>
          </div>

          <!-- 当规则类型为5：异常事故预警时 -->
          <div v-if="rule.ruleValue === '5'">
            <el-form-item label="开启事故预警">
              <el-checkbox v-model="rule.eventDetect">开启事故预警</el-checkbox>
            </el-form-item>
          </div>
        </el-form>
      </el-card>
    </div>

    <!-- 保存与返回按钮 -->
    <el-button type="primary" @click="saveRules">保存规则</el-button>
    <el-button style="margin-left: 10px;" @click="goBack">返回</el-button>

    <!-- 右侧浮动摄像头视图 -->
    <div class="floating-camera">
      <div class="camera-section" ref="floatingCameraContainer">
        <img :src="GetCameraLiveURL(cameraId)" alt="Camera Live" class="camera-image" @load="onFloatingImageLoad" />
        <canvas ref="floatingCanvas" class="drawing-canvas"></canvas>
      </div>
    </div>
  </div>
</template>
<script>
  // 引入相关接口和方法
  import { getCameraRules, updateCameraRules } from '@/api/camera/cameraRules.js'
  import { getLabels } from '@/api/label/label.js'
  import { getCameraLines } from '@/api/camera/cameraLines'
  import { getCameraLiveURL } from '@/api/storage/storage.js'

  export default {
    name: 'cameraRulesView',
    data() {
      return {
        cameraId: '',         // 从路由query中获取
        rules: [],            // 规则列表
        labels: [],           // 可选标签
        cameraLines: [],      // 摄像头检测线列表
        // 浮动摄像头视图的相关数据
        floatingCtx: null,
        floatingCanvasWidth: 640,
        floatingCanvasHeight: 480,
        highlightedLineId: null  // 当前高亮的检测线ID
      }
    },
    created() {
      this.cameraId = this.$route.query.cameraId || ''
      this.fetchRules()
      this.fetchLabels()
      this.fetchCameraLines()
    },
    mounted() {
      this.initFloatingCanvas()
    },
    methods: {
      // 获取摄像头实时画面 URL
      GetCameraLiveURL(cameraId) {
        return getCameraLiveURL(cameraId)
      },
      // 浮动摄像头画面加载完成，设置 canvas 尺寸并重绘检测线
      onFloatingImageLoad(e) {
        const img = e.target
        this.floatingCanvasWidth = img.clientWidth
        this.floatingCanvasHeight = img.clientHeight
        const canvas = this.$refs.floatingCanvas
        canvas.width = this.floatingCanvasWidth
        canvas.height = this.floatingCanvasHeight
        this.redrawFloatingCanvas()
      },
      // 初始化浮动摄像头 canvas
      initFloatingCanvas() {
        const canvas = this.$refs.floatingCanvas
        this.floatingCtx = canvas.getContext('2d')
      },
      // 根据 cameraLines 数据绘制所有检测线，同时高亮选中检测线
      redrawFloatingCanvas() {
        if (!this.floatingCtx) return
        this.floatingCtx.clearRect(0, 0, this.floatingCanvasWidth, this.floatingCanvasHeight)
        this.cameraLines.forEach(line => {
          // 假设接口返回的坐标为相对值（0~1）
          const startX = parseFloat(line.cameraLineStartX) * this.floatingCanvasWidth
          const startY = parseFloat(line.cameraLineStartY) * this.floatingCanvasHeight
          const endX = parseFloat(line.cameraLineEndX) * this.floatingCanvasWidth
          const endY = parseFloat(line.cameraLineEndY) * this.floatingCanvasHeight
          this.floatingCtx.beginPath()
          this.floatingCtx.moveTo(startX, startY)
          this.floatingCtx.lineTo(endX, endY)
          if (line.cameraLineId === this.highlightedLineId) {
            // 高亮样式
            this.floatingCtx.strokeStyle = 'orange'
            this.floatingCtx.lineWidth = 4
          } else {
            // 普通样式
            this.floatingCtx.strokeStyle = 'blue'
            this.floatingCtx.lineWidth = 2
          }
          this.floatingCtx.lineCap = 'round'
          this.floatingCtx.stroke()
        })
      },
      // 当鼠标悬浮到检测线选择框时调用
      handleDetectionLineHover(lineId) {
        if (!lineId) return
        this.highlightedLineId = lineId
        this.redrawFloatingCanvas()
      },
      // 鼠标离开时清除高亮
      clearLineHighlight() {
        this.highlightedLineId = null
        this.redrawFloatingCanvas()
      },
      // 以下为规则相关方法
      fetchRules() {
        if (!this.cameraId) return
        getCameraRules({ cameraId: this.cameraId }).then(response => {
          const data = response.data.data
          this.rules = (data.cameraRules && data.cameraRules.length > 0) ? data.cameraRules.map(rule => {
            return {
              ...rule,
              isNew: false  // 表示该规则是从后端加载的
            }
          }) : []
        }).catch(() => {
          this.$notify.error({
            title: '错误',
            message: '获取规则失败'
          })
        })
      },
      fetchLabels() {
        getLabels().then(response => {
          const data = response.data.data
          this.labels = data.labels || []
        }).catch(() => {
          this.$notify.error({
            title: '错误',
            message: '获取标签失败'
          })
        })
      },
      fetchCameraLines() {
        getCameraLines({ cameraId: this.cameraId }).then(response => {
          const data = response.data.data
          this.cameraLines = data.cameraLines || []
          // 绘制检测线
          this.redrawFloatingCanvas()
        }).catch(() => {
          this.$notify.error({
            title: '错误',
            message: '获取检测线失败'
          })
        })
      },
      addRule() {
        this.rules.push({
          ruleValue: '1',
          label: {
            labelId: [],
            cameraLineId: ''
          },
          isNew: true
        })
      },
      removeRule(index) {
        this.rules.splice(index, 1)
      },
      addLabelsEqual(rule, type) {
        if (type === 'VehicleHold') {
          if (!rule.VehicleHold) {
            this.$set(rule, 'VehicleHold', {
              maxVehicleHoldNum: '',
              maxContinuousTimePeriod: 0,
              minVehicleHoldNum: '',
              minContinuousTimePeriod: 0,
              LabelsEqual: []
            })
          }
          rule.VehicleHold.LabelsEqual.push({ labelId: '', labelHoldNum: '' })
        } else if (type === 'VehicleFlow') {
          if (!rule.VehicleFlow) {
            this.$set(rule, 'VehicleFlow', {
              maxVehicleFlowNum: '',
              maxContinuousTimePeriod: 0,
              minVehicleFlowNum: '',
              minContinuousTimePeriod: 0,
              LabelsEqual: [],
              cameraStartLine: { cameraLineId: '', isAll: false },
              cameraEndLine: { cameraLineId: '', isAll: false }
            })
          }
          rule.VehicleFlow.LabelsEqual.push({ labelId: '', labelEqualNum: '' })
        }
      },
      removeLabelsEqual(labelsEqualArray, index) {
        labelsEqualArray.splice(index, 1)
      },
      saveRules() {
        const payload = {
          cameraId: this.cameraId,
          cameraRules: this.rules.map(rule => {
            // 复制对象，防止直接修改原数据
            let data = { ...rule }
            // 如果规则为新增（即 isNew 为 true）或 cameraRuleId 不存在，则删除 cameraRuleId 字段
            if (rule.isNew || !rule.cameraRuleId) {
              delete data.cameraRuleId
            }
            // 可根据实际情况决定是否保留 isNew 标识，通常不需要传给后端
            delete data.isNew
            return data
          })
        }
        updateCameraRules(payload).then(() => {
          this.$notify.success({
            title: '成功',
            message: '规则更新成功'
          })
        }).catch(() => {
          this.$notify.error({
            title: '失败',
            message: '规则更新失败'
          })
        })
      },
      handleRuleTypeChange(rule) {
        // 根据不同的规则类型初始化或清除对应的属性
        if (rule.ruleValue === '1') {
          if (!rule.label) {
            this.$set(rule, 'label', { labelId: [], cameraLineId: '' });
          }
          if (rule.VehicleHold) {
            delete rule.VehicleHold;
          }
          if (rule.VehicleFlow) {
            delete rule.VehicleFlow;
          }
          if (rule.VehicleReserve !== undefined) {
            delete rule.VehicleReserve;
          }
          if (rule.eventDetect !== undefined) {
            delete rule.eventDetect;
          }
        } else if (rule.ruleValue === '2') {
          this.$set(rule, 'VehicleHold', {
            maxVehicleHoldNum: '',
            maxContinuousTimePeriod: 0,
            minVehicleHoldNum: '',
            minContinuousTimePeriod: 0,
            LabelsEqual: []
          });
          if (rule.VehicleFlow) {
            delete rule.VehicleFlow;
          }
          if (rule.VehicleReserve !== undefined) {
            delete rule.VehicleReserve;
          }
          if (rule.eventDetect !== undefined) {
            delete rule.eventDetect;
          }
        } else if (rule.ruleValue === '3') {
          this.$set(rule, 'VehicleFlow', {
            maxVehicleFlowNum: '',
            maxContinuousTimePeriod: 0,
            minVehicleFlowNum: '',
            minContinuousTimePeriod: 0,
            LabelsEqual: [],
            cameraStartLine: { cameraLineId: '', isAll: false },
            cameraEndLine: { cameraLineId: '', isAll: false }
          });
          if (rule.VehicleHold) {
            delete rule.VehicleHold;
          }
          if (rule.VehicleReserve !== undefined) {
            delete rule.VehicleReserve;
          }
          if (rule.eventDetect !== undefined) {
            delete rule.eventDetect;
          }
        } else if (rule.ruleValue === '4') {
          this.$set(rule, 'VehicleReserve', false);
          if (rule.VehicleHold) { delete rule.VehicleHold; }
          if (rule.VehicleFlow) { delete rule.VehicleFlow; }
          if (rule.eventDetect !== undefined) { delete rule.eventDetect; }
        } else if (rule.ruleValue === '5') {
          this.$set(rule, 'eventDetect', false);
          if (rule.VehicleHold) { delete rule.VehicleHold; }
          if (rule.VehicleFlow) { delete rule.VehicleFlow; }
          if (rule.VehicleReserve !== undefined) { delete rule.VehicleReserve; }
          if (rule.label !== undefined) { delete rule.label; }
        }
      },
      goBack() {
        this.$router.back()
      }
    }
  }
</script>
<style scoped>
  .rules-container {
    padding: 20px;
    position: relative;
  }

  /* 浮动摄像头视图样式 */
  .floating-camera {
    position: fixed;
    top: 100px;
    /* 根据需要调整 */
    right: 20px;
    /* 根据需要调整 */
    width: 640px;
    height: 480px;
    z-index: 999;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
    background: #fff;
  }

  .floating-camera .camera-section {
    position: relative;
    width: 100%;
    height: 100%;
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
    pointer-events: none;
  }

  .rule-card {
    margin-bottom: 20px;
  }

  .labels-equal-item {
    display: flex;
    align-items: center;
    margin-bottom: 10px;
  }
</style>