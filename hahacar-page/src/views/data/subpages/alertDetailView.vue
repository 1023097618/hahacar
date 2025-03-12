<template>
    <div class="alert-detail-container">
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
          <div ref="alertChart" class="alert-chart"></div>
        </div>
      </div>
  
      <!-- 预警信息数据表格 -->
      <el-table v-loading="tableLoading" :data="alertData" border>
        <el-table-column prop="AlertTime" label="预警时间" width="200" />
        <el-table-column prop="AlertNum" label="预警数量" width="150" />
      </el-table>
    </div>
  </template>
  
  <script>
  import * as echarts from 'echarts'
  import { searchAlertNum } from '@/api/stat/alert/alert.js'
  import { getCameraList } from '@/api/camera/camera'
  
  export default {
    name: 'AlertDetailView',
    data() {
      return {
        filterQuery: {
          // 日期时间范围 [开始时间, 结束时间]，由于 value-format 设置成 "yyyy-MM-dd HH:mm:ss"，这里返回的值已是字符串
          timeRange: [],
          // 摄像头多选，存放选中的摄像头 id 数组
          cameraIds: []
        },
        alertData: [],
        tableLoading: false,
        downloadLoading: false,
        // 存放摄像头列表数据，用于下拉框选项
        cameraOptions: [],
        chart: null
      }
    },
    mounted() {
      this.initChart()
      this.getAlertData()
      this.getCameraOptions()
    },
    methods: {
      // 初始化 ECharts 实例
      initChart() {
        this.chart = echarts.init(this.$refs.alertChart)
      },
      // 根据预警数据更新图表
      updateChart() {
        const times = this.alertData.map(item => item.AlertTime)
        const nums = this.alertData.map(item => parseInt(item.AlertNum))
        const option = {
          title: {
            text: '预警信息统计'
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
      // 获取预警信息数据，传递筛选条件
      getAlertData() {
        this.tableLoading = true
        let params = {}
        if (this.filterQuery.timeRange && this.filterQuery.timeRange.length === 2) {
          // 使用已经格式化好的字符串，通过 encodeURIComponent 转码
          params.timeFrom = encodeURIComponent(this.filterQuery.timeRange[0])
          params.timeTo = encodeURIComponent(this.filterQuery.timeRange[1])
        }
        if (this.filterQuery.cameraIds && this.filterQuery.cameraIds.length > 0) {
          params.cameraId = this.filterQuery.cameraIds
        }
        searchAlertNum(params)
          .then(response => {
            const data = response.data.data
            this.alertData = data.alerts || []
            this.updateChart()
            this.tableLoading = false
          })
          .catch(() => {
            this.alertData = []
            this.tableLoading = false
          })
      },
      // 处理搜索按钮点击事件
      handleFilter() {
        this.getAlertData()
      },
      // 导出数据表格（依赖 Export2Excel 插件）
      handleDownload() {
        this.downloadLoading = true
        import('@/vendor/Export2Excel').then(excel => {
          const tHeader = ['预警时间', '预警数量']
          const filterVal = ['AlertTime', 'AlertNum']
          excel.export_json_to_excel2(tHeader, this.alertData, filterVal, '预警信息')
          this.downloadLoading = false
        })
      },
      // 获取摄像头列表，供多选框使用
      getCameraOptions() {
        // 这里假设一次性获取所有摄像头，分页参数可根据实际情况调整
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
  .alert-detail-container {
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
  .alert-chart {
    width: 100%;
    height: 100%;
  }
  </style>
  