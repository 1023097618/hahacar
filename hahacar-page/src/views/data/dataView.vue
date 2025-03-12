<template>
  <div class="data-view-container">
    <div class="charts-grid">
      <!-- 车辆类型分布 -->
      <div class="chart-panel">
        <div class="panel-header">
          <div class="header-right">
            <el-button type="text" class="detail-btn" @click="handleViewDetail('category')">
              查看详细
            </el-button>
          </div>
        </div>
        <div ref="categoryChart" class="chart-box"></div>
      </div>

      <!-- 车流量 -->
      <div class="chart-panel">
        <div class="panel-header">
          <div class="header-right">
            <el-button type="text" class="detail-btn" @click="handleViewDetail('flow')">
              查看详细
            </el-button>
            <el-popover placement="left" width="220" trigger="hover">
              <p>平均多少
                <el-popover placement="top" width="200" trigger="hover">
                  <p>指不同类型的车按照不同的比例折算之后相加的值，可通过摄像头配置页面配置该比例</p>
                  <!-- 用文本作为内层 popover 的触发区域 -->
                  <span slot="reference" style="color: #409EFF; text-decoration: underline; cursor: pointer;">
                    交通当量
                  </span>
                </el-popover>
                通过了路段</p>
              <div slot="reference" class="info-icon">
                <i class="el-icon-question"></i>
              </div>
            </el-popover>
          </div>
        </div>
        <div ref="flowChart" class="chart-box"></div>
      </div>

      <!-- 车辆拥挤度 -->
      <div class="chart-panel">
        <div class="panel-header">
          <div class="header-right">
            <el-button type="text" class="detail-btn" @click="handleViewDetail('hold')">
              查看详细
            </el-button>
            <el-popover placement="left" width="220" trigger="hover">
              <p>平均一帧中有多少
                <el-popover placement="top" width="200" trigger="hover">
                  <p>指不同类型的车按照不同的比例折算之后相加的值，可通过摄像头配置页面配置该比例</p>
                  <!-- 用文本作为内层 popover 的触发区域 -->
                  <span slot="reference" style="color: #409EFF; text-decoration: underline; cursor: pointer;">
                    交通当量
                  </span>
                </el-popover>
              </p>
              <div slot="reference" class="info-icon">
                <i class="el-icon-question"></i>
              </div>
            </el-popover>
          </div>
        </div>
        <div ref="holdChart" class="chart-box"></div>
      </div>

      <!-- 预警信息数量 -->
      <div class="chart-panel">
        <div class="panel-header">
          <div class="header-right">
            <el-button type="text" class="detail-btn" @click="handleViewDetail('alert')">
              查看详细
            </el-button>
          </div>
        </div>
        <div ref="alertChart" class="chart-box"></div>
      </div>
    </div>
  </div>
</template>

<script>
import * as echarts from 'echarts'
import { searchCategoryNum } from '@/api/stat/category/category.js'
import { searchFlowNum } from '@/api/stat/flow/flow.js'
import { searchHoldNum } from '@/api/stat/hold/hold.js'
import { searchAlertNum } from '@/api/stat/alert/alert.js'

export default {
  name: 'dataView',
  data() {
    return {
      // 接口返回的数据
      categoryData: [], // 车辆类型分布
      flowData: [],     // 车流量
      holdData: [],     // 车辆拥挤度
      alertData: [],    // 预警信息数量

      // 查询参数（示例）
      timeFrom: '',
      timeTo: '',
      cameraId: '',
      cameraLineIdStart: '',
      cameraLineIdEnd: '',

      // ECharts 实例
      categoryChart: null,
      flowChart: null,
      holdChart: null,
      alertChart: null
    }
  },
  mounted() {
    // 组件挂载后请求数据
    this.getCategoryData()
    this.getFlowData()
    this.getHoldData()
    this.getAlertData()
  },
  methods: {
    // 点击“查看详细”后调用的方法
    handleViewDetail(type) {
      if(type==="category"){
        this.$router.push("/categoryDetail")
      }else if(type==="alert"){
        this.$router.push("/alertDetail")
      }else if(type==="hold"){
        this.$router.push("/holdDetail")
      }else if(type==="flow"){
        this.$router.push("/flowDetail")
      }
    },

    // 1. 获取车辆类型分布
    async getCategoryData() {
      try {
        const params = {}
        if (this.timeFrom) params.timeFrom = this.timeFrom
        if (this.timeTo) params.timeTo = this.timeTo
        if (this.cameraId) params.cameraId = this.cameraId

        let res = await searchCategoryNum(params)
        res = res.data
        if (res && res.code === '200') {
          this.categoryData = res.data.labels || []
        } else {
          this.categoryData = []
        }
        this.$nextTick(() => {
          this.updateCategoryChart()
        })
      } catch (error) {
        console.error('getCategoryData error:', error)
      }
    },

    // 2. 获取车流量
    async getFlowData() {
      try {
        const params = {}
        if (this.timeFrom) params.timeFrom = this.timeFrom
        if (this.timeTo) params.timeTo = this.timeTo
        if (this.cameraId) params.cameraId = this.cameraId
        if (this.cameraLineIdStart) params.cameraLineIdStart = this.cameraLineIdStart
        if (this.cameraLineIdEnd) params.cameraLineIdEnd = this.cameraLineIdEnd

        let res = await searchFlowNum(params)
        res = res.data
        if (res && res.code === '200') {
          this.flowData = res.data.flows || []
        } else {
          this.flowData = []
        }
        this.$nextTick(() => {
          this.updateFlowChart()
        })
      } catch (error) {
        console.error('getFlowData error:', error)
      }
    },

    // 3. 获取车辆拥挤度
    async getHoldData() {
      try {
        const params = {}
        if (this.timeFrom) params.timeFrom = this.timeFrom
        if (this.timeTo) params.timeTo = this.timeTo
        if (this.cameraId) params.cameraId = this.cameraId

        let res = await searchHoldNum(params)
        res = res.data
        if (res && res.code === '200') {
          this.holdData = res.data.holds || []
        } else {
          this.holdData = []
        }
        this.$nextTick(() => {
          this.updateHoldChart()
        })
      } catch (error) {
        console.error('getHoldData error:', error)
      }
    },

    // 4. 获取预警信息数量
    async getAlertData() {
      try {
        const params = {}
        if (this.timeFrom) params.timeFrom = this.timeFrom
        if (this.timeTo) params.timeTo = this.timeTo
        if (this.cameraId) params.cameraId = this.cameraId

        let res = await searchAlertNum(params)
        res = res.data
        if (res && res.code === '200') {
          this.alertData = res.data.alerts || []
        } else {
          this.alertData = []
        }
        this.$nextTick(() => {
          this.updateAlertChart()
        })
      } catch (error) {
        console.error('getAlertData error:', error)
      }
    },

    // 更新图表函数

    updateCategoryChart() {
      if (!this.$refs.categoryChart) return
      if (!this.categoryChart) {
        this.categoryChart = echarts.init(this.$refs.categoryChart)
      }
      const option = {
        title: { text: '车辆类型分布', left: 'center' },
        tooltip: { trigger: 'item' },
        legend: { bottom: '5%' },
        series: [{
          name: '车辆类型',
          type: 'pie',
          radius: ['40%', '70%'],
          data: this.categoryData.map(item => ({
            name: item.labelName,
            value: item.labelNum
          })),
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0,0,0,0.5)'
            }
          }
        }]
      }
      this.categoryChart.setOption(option)
    },

    updateFlowChart() {
      if (!this.$refs.flowChart) return
      if (!this.flowChart) {
        this.flowChart = echarts.init(this.$refs.flowChart)
      }
      const option = {
        title: { text: '车流量', left: 'center' },
        tooltip: { trigger: 'axis' },
        xAxis: {
          type: 'category',
          data: this.flowData.map(item => item.flowTime)
        },
        yAxis: { type: 'value' },
        series: [{
          name: '车流量',
          type: 'line',
          data: this.flowData.map(item => item.flowNum),
          smooth: true
        }]
      }
      this.flowChart.setOption(option)
    },

    updateHoldChart() {
      if (!this.$refs.holdChart) return
      if (!this.holdChart) {
        this.holdChart = echarts.init(this.$refs.holdChart)
      }
      const option = {
        title: { text: '车辆拥挤度', left: 'center' },
        tooltip: { trigger: 'axis' },
        xAxis: {
          type: 'category',
          data: this.holdData.map(item => item.holdTime)
        },
        yAxis: { type: 'value' },
        series: [{
          name: '拥挤度',
          type: 'line',
          data: this.holdData.map(item => item.holdNum),
          smooth: true
        }]
      }
      this.holdChart.setOption(option)
    },

    updateAlertChart() {
      if (!this.$refs.alertChart) return
      if (!this.alertChart) {
        this.alertChart = echarts.init(this.$refs.alertChart)
      }
      const option = {
        title: { text: '预警信息数量', left: 'center' },
        tooltip: { trigger: 'axis' },
        xAxis: {
          type: 'category',
          data: this.alertData.map(item => item.AlertTime)
        },
        yAxis: { type: 'value' },
        series: [{
          name: '预警数量',
          type: 'line',
          data: this.alertData.map(item => item.AlertNum),
          smooth: true
        }]
      }
      this.alertChart.setOption(option)
    }
  }
}
</script>

<style scoped>
.data-view-container {
  padding: 16px;
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
}

.chart-panel {
  border: 1px solid #eee;
  padding: 16px;
  height: 400px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
}

/* 标题及右侧区域 */
.panel-header {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  margin-bottom: 8px;
}

/* 右侧区域，垂直排列问号图标和按钮 */
.header-right {
  display: flex;
  flex-direction: column;
  align-items: center;
}

/* 问号图标容器 */
.info-icon {
  width: 24px;
  height: 24px;
  background-color: #f2f2f2;
  border-radius: 50%;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.info-icon i {
  font-size: 14px;
  color: #666;
}

/* 查看详细按钮 */
.detail-btn {
  margin-top: 4px;
  padding: 0;
  font-size: 12px;
}

/* 图表容器，自适应剩余空间 */
.chart-box {
  flex: 1;
  width: 100%;
  height: 0;
}
</style>
