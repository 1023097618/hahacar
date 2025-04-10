<template>
  <div class="flow-detail-container">
    <!-- 筛选、操作与图表区域 -->
    <div class="top-bar">
      <!-- 筛选区域 -->
      <div class="filter-container">
        <!-- 第一行：日期、摄像头、多选、搜索与导出 -->
        <div class="filter-top">
          <!-- 日期时间范围筛选 -->
          <el-date-picker
            v-model="filterQuery.timeRange"
            type="datetimerange"
            value-format="yyyy-MM-dd HH:mm:ss"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            class="filter-item"
          />
          <!-- 摄像头多选框 -->
          <el-select
            v-model="filterQuery.cameraIds"
            filterable
            placeholder="请选择摄像头"
            class="filter-item"
            style="width:200px;"
          >
            <el-option
              v-for="camera in cameraOptions"
              :key="camera.cameraId"
              :label="camera.cameraName"
              :value="camera.cameraId"
            />
          </el-select>
        </div>
        <!-- 第二行：检测线筛选模块 -->
        <div class="filter-bottom">
          <!-- 复选框及Popover说明 -->
          <el-checkbox v-model="isDirectionalFlow" class="filter-item">
            定向车流量
          </el-checkbox>
          <el-popover placement="top" trigger="hover">
            <div style="line-height:1.5;">
              勾选后表示车流量为从起始检测线到终止检测线的定向车流量；<br />
              未勾选时表示统计单条检测线的进出流量。
            </div>
            <el-button slot="reference" type="text" icon="el-icon-info"></el-button>
          </el-popover>
          <!-- 根据复选框状态条件显示检测线选择 -->
          <template v-if="!isDirectionalFlow">
            <el-select
              v-model="selectedStartLine"
              filterable
              placeholder="请选择检测线"
              class="filter-item"
              style="width:200px;"
            >
              <el-option
                v-for="line in detectionLineOptions"
                :key="line.cameraLineId"
                :label="line.cameraLineName"
                :value="line.cameraLineId"
              />
            </el-select>
          </template>
          <template v-else>
            <el-select
              v-model="selectedStartLine"
              filterable
              placeholder="请选择起始检测线"
              class="filter-item"
              style="width:200px;"
            >
              <el-option
                v-for="line in detectionLineOptions"
                :key="line.cameraLineId"
                :label="line.cameraLineName"
                :value="line.cameraLineId"
              />
            </el-select>
            <el-select
              v-model="selectedEndLine"
              filterable
              placeholder="请选择终止检测线"
              class="filter-item"
              style="width:200px;"
            >
              <el-option
                v-for="line in detectionLineOptions"
                :key="line.cameraLineId"
                :label="line.cameraLineName"
                :value="line.cameraLineId"
              />
            </el-select>
          </template>
          <el-button type="primary" icon="el-icon-search" class="filter-item" @click="handleFilter">
            搜索
          </el-button>
          <el-button :loading="downloadLoading" type="primary" icon="el-icon-download" class="filter-item" @click="handleDownload">
            导出
          </el-button>
        </div>
      </div>
      <!-- 右侧图表区域 -->
      <div class="chart-container">
        <div ref="flowChart" class="flow-chart"></div>
      </div>
    </div>

    <!-- 车流量数据表格 -->
    <el-table v-loading="tableLoading" :data="flowData" border>
      <el-table-column prop="flowTime" label="流量时间" width="200" />
      <el-table-column prop="flowNum" label="车流量" width="150" />
    </el-table>
  </div>
</template>

<script>
import * as echarts from 'echarts'
import { searchFlowNum } from '@/api/stat/flow/flow.js'
import { getCameraList } from '@/api/camera/camera.js'
import { getCameraLines } from '@/api/camera/cameraLines.js'

export default {
  name: 'FlowDetailView',
  data() {
    return {
      filterQuery: {
        timeRange: [],
        cameraIds: ""
      },
      // 车流量类型：false表示单条检测线（统计进出量），true表示定向（显示起始和终止检测线）
      isDirectionalFlow: false,
      flowData: [],
      tableLoading: false,
      downloadLoading: false,
      cameraOptions: [],
      detectionLineOptions: [],
      selectedStartLine: '',
      selectedEndLine: '',
      chart: null
    }
  },
  watch: {
    'filterQuery.cameraIds'(newVal) {
      if (newVal) {
        this.getDetectionLineOptions(newVal)
      } else {
        this.detectionLineOptions = []
        this.selectedStartLine = ''
        this.selectedEndLine = ''
      }
    }
  },
  mounted() {
    this.initChart()
    this.getFlowData()
    this.getCameraOptions()
  },
  methods: {
    initChart() {
      this.chart = echarts.init(this.$refs.flowChart)
    },
    updateChart() {
      const times = this.flowData.map(item => item.flowTime)
      const nums = this.flowData.map(item => parseInt(item.flowNum))
      const option = {
        title: {
          text: '车流量统计'
        },
        tooltip: {
          trigger: 'axis'
        },
        xAxis: {
          type: 'category',
          data: times
        },
        yAxis: {
          type: 'value'
        },
        series: [
          {
            data: nums,
            type: 'line',
            smooth: true
          }
        ]
      }
      this.chart.setOption(option)
    },
    getFlowData() {
      this.tableLoading = true
      let params = {}
      if (this.filterQuery.timeRange && this.filterQuery.timeRange.length === 2) {
        params.timeFrom = encodeURIComponent(this.filterQuery.timeRange[0])
        params.timeTo = encodeURIComponent(this.filterQuery.timeRange[1])
      }
      if (this.filterQuery.cameraIds && this.filterQuery.cameraIds.length > 0) {
        params.cameraId = this.filterQuery.cameraIds
      }
      // 根据是否定向决定查询参数
      if (this.isDirectionalFlow) {
        if (this.selectedStartLine && this.selectedEndLine) {
          params.cameraLineIdStart = this.selectedStartLine
          params.cameraLineIdEnd = this.selectedEndLine
        }
      } else {
        if (this.selectedStartLine) {
          params.cameraLineId = this.selectedStartLine
        }
      }
      searchFlowNum(params)
        .then(response => {
          const data = response.data.data
          this.flowData = data.flows || []
          this.updateChart()
          this.tableLoading = false
        })
        .catch(() => {
          this.flowData = []
          this.tableLoading = false
        })
    },
    handleFilter() {
      this.getFlowData()
    },
    handleDownload() {
      this.downloadLoading = true
      import('@/vendor/Export2Excel').then(excel => {
        const tHeader = ['流量时间', '车流量']
        const filterVal = ['flowTime', 'flowNum']
        excel.export_json_to_excel2(tHeader, this.flowData, filterVal, '车流量数据')
        this.downloadLoading = false
      })
    },
    getCameraOptions() {
      const params = { pageNum: 1, pageSize: 10000 }
      getCameraList(params)
        .then(response => {
          const data = response.data.data
          this.cameraOptions = data.cameras || []
        })
        .catch(() => {
          this.cameraOptions = []
        })
    },
    getDetectionLineOptions(cameraId) {
      getCameraLines({ cameraId: cameraId })
        .then(response => {
          const data = response.data.data
          this.detectionLineOptions = data.cameraLines || []
        })
        .catch(() => {
          this.detectionLineOptions = []
        })
    }
  }
}
</script>

<style scoped>
.flow-detail-container {
  padding: 20px;
}
.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}
.filter-container {
  display: flex;
  flex-direction: column;
}
.filter-top,
.filter-bottom {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
}
.filter-top {
  margin-bottom: 10px;
}
.filter-item {
  margin-right: 10px;
  margin-bottom: 5px;
}
.chart-container {
  width: 800px;
  height: 250px;
}
.flow-chart {
  width: 100%;
  height: 100%;
}
</style>
