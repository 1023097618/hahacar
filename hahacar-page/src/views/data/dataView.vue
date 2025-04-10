<template>
  <div class="data-view-container">
    <!-- 上面两张图表 -->
    <div class="top-row">
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
    </div>

    <!-- 下面三张图表 -->
    <div class="bottom-row">
      <!-- 和弦图：表示十字路口车流量（带模糊效果） -->
      <div class="chart-panel">
        <div class="panel-header">
          <div class="header-right">
            <el-button type="text" class="detail-btn" @click="handleViewDetail('chord')">
              查看详细
            </el-button>
          </div>
        </div>
        <div ref="chordChart" class="chart-box"></div>
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
import * as d3 from 'd3'
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
    // TODO:FlowData可以画得精确一些，准确来讲后端传过来的是开始时间
    // 组件挂载后请求数据及初始化图表
    this.getCategoryData()
    this.getFlowData()
    this.getHoldData()
    this.getAlertData()
    // // 初始化和弦图（使用 D3-chord 绘制）
    this.$nextTick(() => {
      this.updateChordChart()
    })
  },
  methods: {
    // 点击“查看详细”后调用的方法
    handleViewDetail(type) {
      if (type === "category") {
        this.$router.push("/categoryDetail")
      } else if (type === "alert") {
        this.$router.push("/alertDetail")
      } else if (type === "hold") {
        this.$router.push("/holdDetail")
      } else if (type === "flow") {
        this.$router.push("/flowDetail")
      } else if (type === "chord") {
        this.$router.push("/chordDetail")
      }
    },

    // 1. 获取车辆类型分布数据
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

    // 2. 获取车流量数据
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

    // 3. 获取车辆拥挤度数据
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

    // 4. 获取预警信息数据
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

    // 更新车辆类型分布图（ECharts）
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

    // 更新车流量图（ECharts）
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

    // 更新车辆拥挤度图（ECharts）
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

    // 更新预警信息数量图（ECharts）
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
    },

    // 更新和弦图（使用 D3-chord 绘制）
updateChordChart() {
  if (!this.$refs.chordChart) return;
  // 清空容器
  d3.select(this.$refs.chordChart).selectAll("*").remove();

  // 获取容器尺寸
  const width = this.$refs.chordChart.clientWidth || 400;
  const height = this.$refs.chordChart.clientHeight || 400;
  const outerRadius = Math.min(width, height) * 0.5 - 40;
  const innerRadius = outerRadius - 30;

  // 创建 SVG 容器
  const svgContainer = d3.select(this.$refs.chordChart)
    .append("svg")
    .attr("width", width)
    .attr("height", height);

  // 定义模糊滤镜，仅应用于和弦图部分
  const defs = svgContainer.append("defs");
  const filter = defs.append("filter")
    .attr("id", "blurFilter");
  filter.append("feGaussianBlur")
    .attr("in", "SourceGraphic")
    .attr("stdDeviation", 4);

  // 添加标题文本（不应用滤镜）
  svgContainer.append("text")
    .attr("x", width / 2)
    .attr("y", 20)
    .attr("text-anchor", "middle")
    .style("fill", "rgb(70,70,70)")
    .style("font-size", "18px")
    .style("font-family", "sans-serif")
    .style("font-weight", "bold")
    .text("十字路口车流量和弦图（单向流）");

  // 创建一个 g 元素用于绘制和弦图
  const g = svgContainer.append("g")
  .attr("filter", "url(#blurFilter)")
    .attr("transform", `translate(${width / 2}, ${height / 2})`);

  // 原始数据矩阵：表示四个方向之间的流量
  const matrix = [
    [0, 50, 200, 20],
    [40, 0, 60, 30],
    [20, 70, 0, 80],
    [30, 40, 90, 0]
  ];

  // 使用 d3.chordDirected 生成单向流的和弦数据
  const chordGenerator = d3.chordDirected()
    .padAngle(0.05)
    .sortSubgroups(d3.descending);
  const chords = chordGenerator(matrix);

  // 定义颜色映射（4个分组）
  const color = d3.scaleOrdinal()
    .domain(d3.range(matrix.length))
    .range(["#FF5733", "#33FF57", "#3357FF", "#FF33A1"]);

  // 弧线生成器
  const arcGenerator = d3.arc()
    .innerRadius(innerRadius)
    .outerRadius(outerRadius);

  // 绘制分组弧线
  const group = g.append("g")
    .selectAll("g")
    .data(chords.groups)
    .enter().append("g");

  group.append("path")
    .style("fill", d => color(d.index))
    .style("stroke", d => d3.rgb(color(d.index)).darker())
    .attr("d", arcGenerator);

  // 添加分组标签
  const labels = ["North", "East", "South", "West"];
  group.append("text")
    .each(function(d) { d.angle = (d.startAngle + d.endAngle) / 2; })
    .attr("dy", ".35em")
    .attr("transform", function(d) {
      return "rotate(" + (d.angle * 180 / Math.PI - 90) + ")"
        + " translate(" + (outerRadius + 10) + ")"
        + (d.angle > Math.PI ? " rotate(180)" : "");
    })
    .attr("text-anchor", d => d.angle > Math.PI ? "end" : "start")
    .text((d, i) => labels[i]);

  // 绘制和弦（弦带），应用模糊滤镜
  g.append("g")
    .attr("fill-opacity", 0.7)
    .selectAll("path")
    .data(chords)
    .enter().append("path")
    .attr("d", d3.ribbon().radius(innerRadius))
    .style("fill", d => color(d.source.index))
    .style("stroke", d => d3.rgb(color(d.source.index)).darker());
}
  }
}
</script>

<style scoped>
.data-view-container {
  padding: 16px;
}

/* 上面两行、下面三行 */
.top-row,
.bottom-row {
  display: flex;
  gap: 24px;
}

.bottom-row {
  margin-top: 24px;
}

/* 每个图表面板 */
.chart-panel {
  flex: 1;
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

/* 右侧区域，垂直排列 */
.header-right {
  display: flex;
  flex-direction: column;
  align-items: center;
}

/* 问号图标 */
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

/* 图表容器 */
.chart-box {
  flex: 1;
  width: 100%;
  height: 100%;
}
</style>
