<template>
  <div class="chord-detail-container">
    <!-- 筛选、操作与图表区域 -->
    <div class="top-bar">
      <!-- 筛选与操作区域 -->
      <div class="filter-container">
        <!-- 日期时间范围筛选 -->
        <el-date-picker v-model="filterQuery.timeRange" type="datetimerange" value-format="yyyy-MM-dd HH:mm:ss"
          start-placeholder="开始日期" end-placeholder="结束日期" class="filter-item" />
        <!-- 摄像头下拉选择 -->
        <el-select v-model="filterQuery.cameraId" filterable placeholder="请选择摄像头" class="filter-item"
          style="width:200px;">
          <el-option v-for="camera in cameraOptions" :key="camera.cameraId" :label="camera.cameraName"
            :value="camera.cameraId" />
        </el-select>
        <el-button type="primary" icon="el-icon-search" class="filter-item" @click="handleFilter">
          搜索
        </el-button>
        <el-button :loading="downloadLoading" type="primary" icon="el-icon-download" class="filter-item"
          @click="handleDownload">
          导出
        </el-button>
      </div>
      <!-- 图表区域 -->
      <div class="chart-container" ref="chordChart"></div>
    </div>
    <!-- 数据表格区域 -->
    <div class="table-container" v-loading="tableLoading">
      <div class="table-caption">
        起点：左侧；终点：顶部
      </div>
      <table class="flow-matrix">
        <thead>
          <tr>
            <!-- 左上角空白 -->
            <th></th>
            <th v-for="(line) in cameraLines" :key="line.cameraLineId">
              {{ line.cameraLineName }}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(line, rowIndex) in cameraLines" :key="line.cameraLineId">
            <th class="row-header">
              {{ line.cameraLineName }}
              <!-- 行展开按钮，点击后箭头图标旋转 -->
              <el-button type="text" icon="el-icon-arrow-down" @click="toggleRowExpand(rowIndex)"
                :class="{ expanded: expandedRows[rowIndex] }" class="row-toggle"></el-button>
            </th>
            <td v-for="(cell, colIndex) in aggregatedMatrix[rowIndex]" :key="colIndex">
              <div class="cell-value">
                <span>{{ cell.sum }}</span>
              </div>
              <!-- 当本行展开时，各单元格显示明细 -->
              <div v-if="expandedRows[rowIndex]" class="cell-details">
                <div v-for="(detail, index) in cell.details" :key="index">
                  {{ labels[index].labelName }}: {{ detail }}
                </div>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
  import * as d3 from "d3";
  import { getFlowMat } from "@/api/stat/flow/flow.js";
  import { getCameraList } from "@/api/camera/camera";

  export default {
    name: "chordDetailView",
    data() {
      return {
        filterQuery: {
          timeRange: [],
          cameraId: ""
        },
        tableLoading: false,
        downloadLoading: false,
        cameraOptions: [],
        cameraLines: [],
        labels: [],
        flowmat: [], // 原始接口返回的 3D 矩阵数据
        aggregatedMatrix: [], // 处理后的二维矩阵，每个单元格包含 { sum, details }
        expandedRows: [] // 控制每一行展开（true 展开，false 收起）
      };
    },
    mounted() {
      // 初始时只渲染空的图表，不调用 getFlowMatData
      this.updateChordChart();
      this.getCameraOptions();
    },
    methods: {
      // 更新和弦图
      updateChordChart() {
        if (!this.$refs.chordChart) return;
        // 清空容器
        d3.select(this.$refs.chordChart).selectAll("*").remove();

        // 获取容器尺寸（如未设置，则默认 400*400）
        const width = this.$refs.chordChart.clientWidth || 400;
        const height = this.$refs.chordChart.clientHeight || 400;

        // 适当减小外圆半径，避免文字被裁剪
        const outerRadius = Math.min(width, height) * 0.5 - 40;
        const innerRadius = outerRadius - 30;

        // 创建 SVG 容器
        const svgContainer = d3.select(this.$refs.chordChart)
          .append("svg")
          .attr("width", width)
          .attr("height", height);

        // 添加标题文本
        svgContainer.append("text")
          .attr("x", width / 2)
          .attr("y", 20)
          .attr("text-anchor", "middle")
          .style("fill", "rgb(70,70,70)")
          .style("font-size", "18px")
          .style("font-family", "sans-serif")
          .style("font-weight", "bold")
          .text("检测线车流量和弦图");

        // 创建一个 g 元素用于绘制和弦图
        const g = svgContainer.append("g")
          .attr("transform", `translate(${width / 2}, ${height / 2})`);

        // 构造二维数值矩阵
        const matrix = this.aggregatedMatrix.map(row => row.map(cell => cell.sum));
        if (matrix.length === 0) return;

        // 生成和弦数据
        const chordGenerator = d3.chordDirected()
          .padAngle(0.05)
          .sortSubgroups(d3.descending);

        const chords = chordGenerator(matrix);

        // 定义颜色映射（可自行增减颜色）
        const color = d3.scaleOrdinal()
          .domain(d3.range(matrix.length))
          .range(["#FF5733", "#33FF57", "#3357FF", "#FF33A1", "#FFC300", "#00BFFF"]);

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
        group.append("text")
          .each(function (d) { d.angle = (d.startAngle + d.endAngle) / 2; })
          .attr("dy", ".35em")
          .attr("transform", d => {
            return (
              "rotate(" + (d.angle * 180 / Math.PI - 90) + ")" +
              " translate(" + (outerRadius + 10) + ")" +
              (d.angle > Math.PI ? " rotate(180)" : "")
            );
          })
          .style("font-size", "12px")
          .attr("text-anchor", d => (d.angle > Math.PI ? "end" : "start"))
          .text((d, i) => {
            return this.cameraLines[i]?.cameraLineName || "";
          });

        // 绘制和弦（弦带），颜色由“源”检测线决定
        const ribbons = g.append("g")
          .attr("fill-opacity", 0.7)
          .selectAll("path")
          .data(chords)
          .enter().append("path")
          .attr("d", d3.ribbon().radius(innerRadius))
          .style("fill", d => color(d.source.index)) // 以 source.index 为主
          .style("stroke", d => d3.rgb(color(d.source.index)).darker());

        // 新增 tooltip，用于显示和弦详细信息
        const tooltip = d3.select(this.$refs.chordChart)
          .append("div")
          .attr("class", "tooltip")
          .style("position", "absolute")
          .style("padding", "5px")
          .style("background", "rgba(0,0,0,0.7)")
          .style("color", "#fff")
          .style("border-radius", "4px")
          .style("pointer-events", "none")
          .style("display", "none")
          .style("max-width", "200px");

        // 鼠标事件：高亮当前弦，并显示 tooltip
        const self = this;
        ribbons.on("mouseover", function (event, d) {
          d3.select(this).style("stroke-width", "3px");
          const sourceIndex = d.source.index;
          const targetIndex = d.target.index;
          const cell = self.aggregatedMatrix[sourceIndex][targetIndex];
          let tooltipText = `从 ${self.cameraLines[sourceIndex]?.cameraLineName || ""} 到 ${self.cameraLines[targetIndex]?.cameraLineName || ""}<br>`;
          tooltipText += `总数: ${cell.sum}<br>`;
          self.labels.forEach((label, idx) => {
            tooltipText += `${label.labelName}: ${cell.details[idx]}<br>`;
          });
          tooltip.html(tooltipText).style("display", "block");
        })
          .on("mousemove", function (event) {
            const containerRect = self.$refs.chordChart.getBoundingClientRect()
            tooltip.style('left', (event.clientX - containerRect.left + 10) + 'px')
              .style('top', (event.clientY - containerRect.top + 10) + 'px')
          })
          .on("mouseout", function () {
            d3.select(this).style("stroke-width", null);
            tooltip.style("display", "none");
          });
      },

      // 点击搜索按钮时请求接口获取数据
      getFlowMatData() {
        this.tableLoading = true;
        let params = {};
        if (this.filterQuery.timeRange && this.filterQuery.timeRange.length === 2) {
          params.timeFrom = encodeURIComponent(this.filterQuery.timeRange[0]);
          params.timeTo = encodeURIComponent(this.filterQuery.timeRange[1]);
        }
        if (this.filterQuery.cameraId) {
          params.cameraId = this.filterQuery.cameraId;
        }
        getFlowMat(params)
          .then(response => {
            const data = response.data.data;
            this.flowmat = data.flowmat || [];
            this.cameraLines = data.cameraLines || [];
            this.labels = data.labels || [];
            // 处理 3D 矩阵数据
            this.processFlowMat();
            // 更新弦图
            this.updateChordChart();
            this.tableLoading = false;
          })
          .catch(() => {
            this.flowmat = [];
            this.cameraLines = [];
            this.labels = [];
            this.aggregatedMatrix = [];
            this.tableLoading = false;
          });
      },

      // 将接口返回的 3D 矩阵（[i][j][k]）处理为每个单元格 { sum, details }
      processFlowMat() {
        let matrix = [];
        for (let i = 0; i < this.cameraLines.length; i++) {
          matrix[i] = [];
          for (let j = 0; j < this.cameraLines.length; j++) {
            let sum = 0;
            let details = [];
            for (let k = 0; k < this.labels.length; k++) {
              // 直接使用后端返回的数据，不交换索引
              let val = parseFloat(this.flowmat[i][j][k]) || 0;
              details.push(val);
              sum += val;
            }
            matrix[i][j] = { sum, details };
          }
        }
        this.aggregatedMatrix = matrix;
        // 初始化每一行的展开状态
        this.expandedRows = Array(this.cameraLines.length).fill(false);
      },

      // 切换某一行展开/收起状态（带动画效果）
      toggleRowExpand(rowIndex) {
        this.$set(this.expandedRows, rowIndex, !this.expandedRows[rowIndex]);
      },

      // 点击搜索按钮时调用
      handleFilter() {
        this.getFlowMatData();
      },

      // 导出数据
      handleDownload() {
        this.downloadLoading = true;
        import("@/vendor/Export2Excel").then(excel => {
          const header = ["起点", "终点", "总数", ...this.labels.map(label => label.labelName)];
          const exportData = [];
          for (let i = 0; i < this.cameraLines.length; i++) {
            for (let j = 0; j < this.cameraLines.length; j++) {
              let record = {
                "起点": this.cameraLines[i].cameraLineName,
                "终点": this.cameraLines[j].cameraLineName,
                "总数": this.aggregatedMatrix[i][j].sum
              };
              this.labels.forEach((label, idx) => {
                record[label.labelName] = this.aggregatedMatrix[i][j].details[idx];
              });
              exportData.push(record);
            }
          }
          excel.export_json_to_excel2(header, exportData, header, "车流矩阵数据");
          this.downloadLoading = false;
        });
      },

      // 获取摄像头下拉列表
      getCameraOptions() {
        const params = { pageNum: 1, pageSize: 10000 };
        getCameraList(params)
          .then(response => {
            const data = response.data.data;
            this.cameraOptions = data.cameras || [];
          })
          .catch(() => {
            this.cameraOptions = [];
          });
      }
    }
  };
</script>

<style>
  .chord-detail-container {
    padding: 20px;
  }

  .top-bar {
    display: flex;
    flex-direction: column;
    margin-bottom: 20px;
  }

  .filter-container {
    display: flex;
    align-items: center;
    margin-bottom: 20px;
  }

  .filter-item {
    margin-right: 10px;
  }

  .chart-container {
    width: 400px;
    /* 可以根据需要调大或调小 */
    height: 400px;
    margin: auto;
    position: relative;
  }

  .table-container {
    margin-top: 20px;
    overflow-x: auto;
  }

  .table-caption {
    text-align: center;
    margin-bottom: 5px;
    font-weight: bold;
  }

  .flow-matrix {
    width: 100%;
    border-collapse: collapse;
    text-align: center;
  }

  .flow-matrix th,
  .flow-matrix td {
    border: 1px solid #ebeef5;
    padding: 8px;
  }

  .row-header {
    position: relative;
  }

  .row-toggle {
    margin-left: 5px;
    transition: transform 0.3s ease;
  }

  .row-toggle.expanded {
    transform: rotate(180deg);
  }

  .cell-value {
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .cell-details {
    margin-top: 5px;
    font-size: 12px;
    color: #606266;
  }

  .tooltip {
    pointer-events: none;
    font-size: 12px;
    background: rgba(0, 0, 0, 0.7);
    color: #fff;
    padding: 5px;
    border-radius: 4px;
    z-index: 9999;
    width: 100px;
  }
</style>