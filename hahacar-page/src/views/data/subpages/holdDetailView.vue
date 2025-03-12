<template>
  <div class="hold-detail-container">
    <!-- 筛选、操作与图表区域 -->
    <div class="top-bar">
      <!-- 筛选与操作区域 -->
      <div class="filter-container">
        <!-- 日期时间范围筛选 -->
        <el-date-picker
          v-model="filterQuery.timeRange"
          type="datetimerange"
          value-format="yyyy-MM-dd HH:mm:ss"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          class="filter-item"
        />
        <!-- 摄像头多选框：根据摄像头名称进行筛选 -->
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
        <el-button type="primary" icon="el-icon-search" class="filter-item" @click="handleFilter">
          搜索
        </el-button>
        <el-button :loading="downloadLoading" type="primary" icon="el-icon-download" class="filter-item" @click="handleDownload">
          导出
        </el-button>
      </div>
      <!-- 右侧图表区域 -->
      <div class="chart-container">
        <div ref="holdChart" class="hold-chart"></div>
      </div>
    </div>

    <!-- 拥堵情况数据表格 -->
    <el-table v-loading="tableLoading" :data="holdData" border>
      <el-table-column prop="holdTime" label="拥堵时间" width="200" />
      <el-table-column prop="holdNum" label="拥堵值" width="150" />
    </el-table>
  </div>
</template>

<script>
import * as echarts from 'echarts'
import { searchHoldNum } from '@/api/stat/hold/hold.js'
import { getCameraList } from '@/api/camera/camera'

export default {
  name: 'HoldDetailView',
  data() {
    return {
      filterQuery: {
        // 日期时间范围 [开始时间, 结束时间]
        timeRange: [],
        // 摄像头多选，存放选中的摄像头 id 数组
        cameraIds: []
      },
      holdData: [],
      tableLoading: false,
      downloadLoading: false,
      // 摄像头列表，用于下拉框选项
      cameraOptions: [],
      chart: null
    }
  },
  mounted() {
    this.initChart()
    this.getHoldData()
    this.getCameraOptions()
  },
  methods: {
    // 初始化 ECharts 实例
    initChart() {
      this.chart = echarts.init(this.$refs.holdChart)
    },
    // 根据拥堵数据更新图表
    updateChart() {
      const times = this.holdData.map(item => item.holdTime)
      const nums = this.holdData.map(item => parseInt(item.holdNum))
      const option = {
        title: {
          text: '拥堵情况统计'
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
    // 获取拥堵数据，传递筛选条件
    getHoldData() {
      this.tableLoading = true
      let params = {}
      if (this.filterQuery.timeRange && this.filterQuery.timeRange.length === 2) {
        params.timeFrom = encodeURIComponent(this.filterQuery.timeRange[0])
        params.timeTo = encodeURIComponent(this.filterQuery.timeRange[1])
      }
      if (this.filterQuery.cameraIds && this.filterQuery.cameraIds.length > 0) {
        params.cameraId = this.filterQuery.cameraIds
      }
      searchHoldNum(params)
        .then(response => {
          const data = response.data.data
          this.holdData = data.holds || []
          this.updateChart()
          this.tableLoading = false
        })
        .catch(() => {
          this.holdData = []
          this.tableLoading = false
        })
    },
    // 处理搜索按钮点击事件
    handleFilter() {
      this.getHoldData()
    },
    // 导出数据表格（依赖 Export2Excel 插件）
    handleDownload() {
      this.downloadLoading = true
      import('@/vendor/Export2Excel').then(excel => {
        const tHeader = ['拥堵时间', '拥堵值']
        const filterVal = ['holdTime', 'holdNum']
        excel.export_json_to_excel2(tHeader, this.holdData, filterVal, '拥堵情况')
        this.downloadLoading = false
      })
    },
    // 获取摄像头列表，供多选框使用
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
    }
  }
}
</script>

<style scoped>
.hold-detail-container {
  padding: 20px;
}
.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.filter-container {
  display: flex;
  align-items: center;
}
.filter-item {
  margin-right: 10px;
}
.chart-container {
  width: 800px;
  height: 250px;
}
.hold-chart {
  width: 100%;
  height: 100%;
}
</style>
