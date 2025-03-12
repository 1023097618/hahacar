<template>
  <div class="category-detail-container">
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
        <!-- 摄像头多选：根据摄像头名称进行筛选 -->
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
      <!-- 图表区域 -->
      <div class="chart-container">
        <div ref="categoryChart" class="category-chart"></div>
      </div>
    </div>
    <!-- 数据表格 -->
    <el-table v-loading="tableLoading" :data="categoryData" border>
      <el-table-column prop="labelName" label="车辆类型" width="200" />
      <el-table-column prop="labelNum" label="数量" width="150" />
    </el-table>
  </div>
</template>

<script>
import * as echarts from 'echarts'
import { searchCategoryNum } from '@/api/stat/category/category.js'
import { getCameraList } from '@/api/camera/camera'

export default {
  name: 'CategoryDetailView',
  data() {
    return {
      filterQuery: {
        // 日期时间范围 [开始时间, 结束时间]，格式为 "yyyy-MM-dd HH:mm:ss"
        timeRange: [],
        // 摄像头多选，存放选中的摄像头 id 数组
        cameraIds: []
      },
      // 存放返回的车辆类别数据，接口返回 data.labels 数组，每项包含 labelName 和 labelNum
      categoryData: [],
      tableLoading: false,
      downloadLoading: false,
      // 摄像头下拉框数据
      cameraOptions: [],
      chart: null
    }
  },
  mounted() {
    this.initChart()
    this.getCategoryData()
    this.getCameraOptions()
  },
  methods: {
    // 初始化 ECharts 实例
    initChart() {
      this.chart = echarts.init(this.$refs.categoryChart)
    },
    // 根据车辆类别数据更新饼图
    updateChart() {
      // 将接口返回的 labelNum 转换为数值
      const data = this.categoryData.map(item => ({
        value: parseInt(item.labelNum),
        name: item.labelName
      }))
      const option = {
        title: {
          text: '车辆种类统计',
          left: 'center'
        },
        tooltip: {
          trigger: 'item'
        },
        legend: {
          orient: 'vertical',
          left: 'left'
        },
        series: [
          {
            name: '车辆数量',
            type: 'pie',
            radius: '50%',
            data: data,
            emphasis: {
              itemStyle: {
                shadowBlur: 10,
                shadowOffsetX: 0,
                shadowColor: 'rgba(0, 0, 0, 0.5)'
              }
            }
          }
        ]
      }
      this.chart.setOption(option)
    },
    // 获取车辆类别数据，调用 searchCategoryNum 接口
    getCategoryData() {
      this.tableLoading = true
      let params = {}
      if (this.filterQuery.timeRange && this.filterQuery.timeRange.length === 2) {
        // 使用格式化好的字符串，通过 encodeURIComponent 转码
        params.timeFrom = encodeURIComponent(this.filterQuery.timeRange[0])
        params.timeTo = encodeURIComponent(this.filterQuery.timeRange[1])
      }
      if (this.filterQuery.cameraIds && this.filterQuery.cameraIds.length > 0) {
        // 若选中多个摄像头，可考虑做拼接或仅取第一个（这里示例取第一个）
        params.cameraId = this.filterQuery.cameraIds[0]
      }
      searchCategoryNum(params)
        .then(response => {
          const data = response.data.data
          this.categoryData = data.labels || []
          this.updateChart()
          this.tableLoading = false
        })
        .catch(() => {
          this.categoryData = []
          this.tableLoading = false
        })
    },
    // 处理搜索按钮点击事件
    handleFilter() {
      this.getCategoryData()
    },
    // 导出数据表格（依赖 Export2Excel 插件）
    handleDownload() {
      this.downloadLoading = true
      import('@/vendor/Export2Excel').then(excel => {
        const tHeader = ['车辆类型', '数量']
        const filterVal = ['labelName', 'labelNum']
        excel.export_json_to_excel2(tHeader, this.categoryData, filterVal, '车辆种类信息')
        this.downloadLoading = false
      })
    },
    // 获取摄像头列表供筛选使用
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
.category-detail-container {
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
.category-chart {
  width: 100%;
  height: 100%;
}
</style>
