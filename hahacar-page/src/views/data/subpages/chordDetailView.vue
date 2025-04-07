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
        flowmat: [], // 接口返回的 3D 矩阵数据
        aggregatedMatrix: [], // 转换为表格展示的二维矩阵，每个单元包含 { sum, details }
        expandedRows: [] // 控制每行展开与否
      };
    },
    mounted() {
      // 初始化时绘制弦图，如果没有数据则不会渲染
      this.drawChordDiagram();
      this.getCameraOptions();
    },
    methods: {
      drawChordDiagram() {
        // 如果接口数据不足或者检测线数量小于2，则不绘制弦图
        if (
          !this.cameraLines ||
          !this.cameraLines.length ||
          !this.flowmat ||
          !this.flowmat.length ||
          !this.labels ||
          !this.labels.length ||
          this.cameraLines.length < 2
        ) {
          return;
        }

        // 清空容器内内容
        d3.select(this.$refs.chordChart).selectAll("*").remove();

        const container = this.$refs.chordChart;
        const width = container.clientWidth || 800;
        const height = container.clientHeight || 800;
        const innerRadius = Math.min(width, height) * 0.4;
        const outerRadius = innerRadius * 1.1;

        // 直接使用接口返回的数据，不设置默认值
        const cameraLines = this.cameraLines.map(item => item.cameraLineName);
        const vehicleTypes = this.labels.map(item => item.labelName);
        const vehicleEquivalents = this.flowmat.map(row =>
          row.map(cell => cell.map(val => parseFloat(val)))
        );

        // 定义颜色映射
        const color = d3.scaleOrdinal()
          .domain(cameraLines)
          .range(["#80cbc4", "#a5d6a7", "#fff59d", "#90caf9"]);
        const vehicleTypeColors = d3.scaleOrdinal()
          .domain(vehicleTypes)
          .range(["#ef5350", "#ab47bc", "#42a5f5", "#26a69a"]);

        // 根据当前车辆类型（或总和）计算矩阵
        function computeMatrix(selectedType) {
          const m = [];
          for (let i = 0; i < cameraLines.length; i++) {
            m[i] = [];
            for (let j = 0; j < cameraLines.length; j++) {
              let value = 0;
              if (selectedType === null) {
                value = d3.sum(vehicleEquivalents[i][j]);
              } else {
                value = vehicleEquivalents[i][j][selectedType];
              }
              // 对角线置为 0
              if (i === j) value = 0;
              m[i][j] = value;
            }
          }
          return m;
        }

        let activeVehicleType = null;
        let currentMatrix = computeMatrix(null);

        // 构造 chord 布局
        const chordGenerator = d3.chordDirected()
          .padAngle(0.05)
          .sortSubgroups(d3.descending);
        let chordsData = chordGenerator(currentMatrix);

        const arc = d3.arc()
          .innerRadius(innerRadius)
          .outerRadius(outerRadius);
        const ribbon = d3.ribbon()
          .radius(innerRadius);

        const svg = d3.select(container)
          .append("svg")
          .attr("width", width)
          .attr("height", height)
          .attr("viewBox", [-width / 2, -height / 2, width, height]);

        // 新建 tooltip
        const tooltip = d3.select(container)
          .append("div")
          .attr("class", "chord-tooltip")
          .style("position", "absolute")
          .style("padding", "8px")
          .style("background", "#ffffff")
          .style("border", "1px solid #80cbc4")
          .style("border-radius", "4px")
          .style("pointer-events", "none")
          .style("font-size", "12px")
          .style("box-shadow", "0 2px 4px rgba(0,0,0,0.1)")
          .style("visibility", "hidden");

        // 辅助函数：更新 tooltip 位置，确保相对于父容器定位
        function updateTooltipPosition(event) {
          const containerRect = container.getBoundingClientRect();
          tooltip.style("top", (event.clientY - containerRect.top - 10) + "px")
            .style("left", (event.clientX - containerRect.left + 10) + "px");
        }

        // 绘制外侧群组弧（表示各检测线）
        const groupArcs = svg.append("g")
          .selectAll("path")
          .data(chordsData.groups)
          .join("path")
          .attr("d", arc)
          .attr("fill", d => color(cameraLines[d.index]))
          .attr("stroke", "#ffffff")
          .attr("stroke-width", 1)
          .style("opacity", 0.8)
          .on("click", () => {
            if (activeVehicleType !== null) {
              activeVehicleType = null;
              updateChords();
              updateOuterSegments();
            }
          })
          .on("mouseover", (event, d) => {
            const idx = d.index;
            // 计算出流量
            let outgoingTotal = 0;
            let outgoingBreakdown = new Array(vehicleTypes.length).fill(0);
            for (let j = 0; j < cameraLines.length; j++) {
              if (idx !== j) {
                let arr = vehicleEquivalents[idx][j];
                outgoingTotal += arr.reduce((sum, val) => sum + val, 0);
                for (let k = 0; k < vehicleTypes.length; k++) {
                  outgoingBreakdown[k] += arr[k];
                }
              }
            }
            // 计算进流量
            let incomingTotal = 0;
            let incomingBreakdown = new Array(vehicleTypes.length).fill(0);
            for (let j = 0; j < cameraLines.length; j++) {
              if (idx !== j) {
                let arr = vehicleEquivalents[j][idx];
                incomingTotal += arr.reduce((sum, val) => sum + val, 0);
                for (let k = 0; k < vehicleTypes.length; k++) {
                  incomingBreakdown[k] += arr[k];
                }
              }
            }
            let total = outgoingTotal + incomingTotal;
            let html = `<strong>${cameraLines[idx]}</strong><br>`;
            html += `<u>出流量</u>: ${outgoingTotal}<br>`;
            vehicleTypes.forEach((type, i) => {
              html += `${type}: ${outgoingBreakdown[i]}<br>`;
            });
            html += `<u>进流量</u>: ${incomingTotal}<br>`;
            vehicleTypes.forEach((type, i) => {
              html += `${type}: ${incomingBreakdown[i]}<br>`;
            });
            html += `<u>总流量</u>: ${total}`;
            tooltip.html(html).style("visibility", "visible");
            updateTooltipPosition(event);
          })
          .on("mousemove", (event) => {
            updateTooltipPosition(event);
          })
          .on("mouseout", () => {
            tooltip.style("visibility", "hidden");
          });

        // 绘制连接各检测线的弦 Ribbon
        let ribbons = svg.append("g")
          .selectAll("path")
          .data(chordsData)
          .join("path")
          .attr("d", ribbon)
          .attr("fill", d => color(cameraLines[d.source.index]))
          .attr("stroke", "#ddd")
          .style("opacity", 0.7)
          .style("mix-blend-mode", "multiply")
          .on("mouseover", (event, d) => {
            d3.select(event.currentTarget).style("opacity", 1);
            let html = "";
            if (activeVehicleType === null) {
              const breakdown = vehicleEquivalents[d.source.index][d.target.index];
              const total = breakdown.reduce((a, b) => a + b, 0);
              html = `<strong>${cameraLines[d.source.index]} → ${cameraLines[d.target.index]}</strong><br>
                    总流量: ${total}<br>`;
              breakdown.forEach((val, idx) => {
                html += `${vehicleTypes[idx]}: ${val}<br>`;
              });
            } else {
              html = `<strong>${cameraLines[d.source.index]} → ${cameraLines[d.target.index]}</strong><br>
                    ${vehicleTypes[activeVehicleType]} 流量: ${vehicleEquivalents[d.source.index][d.target.index][activeVehicleType]}`;
            }
            tooltip.html(html).style("visibility", "visible");
            updateTooltipPosition(event);
          })
          .on("mousemove", (event) => {
            updateTooltipPosition(event);
          })
          .on("mouseout", function () {
            d3.select(this).style("opacity", 0.7);
            tooltip.style("visibility", "hidden");
          })
          .on("click", () => {
            if (activeVehicleType !== null) {
              activeVehicleType = null;
              updateChords();
              updateOuterSegments();
            }
          });

        // 绘制外侧按车辆类型分段
        const outerGroup = svg.append("g")
          .attr("class", "outer-segments");

        function updateOuterSegments() {
          const segmentsData = [];
          for (let i = 0; i < cameraLines.length; i++) {
            let total = 0;
            let typeValues = [];
            for (let k = 0; k < vehicleTypes.length; k++) {
              let sumForType = 0;
              for (let j = 0; j < cameraLines.length; j++) {
                if (i === j) continue;
                sumForType += vehicleEquivalents[i][j][k];
              }
              typeValues.push(sumForType);
              total += sumForType;
            }
            const groupData = chordsData.groups.find(g => g.index === i);
            if (groupData) {
              // 如果总和为0，避免除零，直接将所有分段角度设为0
              if (total === 0) {
                for (let k = 0; k < vehicleTypes.length; k++) {
                  segmentsData.push({
                    index: i,
                    typeIndex: k,
                    type: vehicleTypes[k],
                    value: 0,
                    startAngle: groupData.startAngle,
                    endAngle: groupData.startAngle,
                    padAngle: groupData.padAngle
                  });
                }
                continue;
              }
              let startAngle = groupData.startAngle;
              for (let k = 0; k < vehicleTypes.length; k++) {
                const angle = (groupData.endAngle - groupData.startAngle) * (typeValues[k] / total);
                const endAngle = startAngle + angle;
                segmentsData.push({
                  index: i,
                  typeIndex: k,
                  type: vehicleTypes[k],
                  value: typeValues[k],
                  startAngle: startAngle,
                  endAngle: endAngle,
                  padAngle: groupData.padAngle
                });
                startAngle = endAngle;
              }
            }
          }
          const segments = outerGroup.selectAll("path")
            .data(segmentsData, d => d.index + "-" + d.typeIndex);

          segments.transition().duration(300)
            .attr("d", d3.arc()
              .innerRadius(outerRadius + 6)
              .outerRadius(outerRadius + 20)
              .startAngle(d => d.startAngle)
              .endAngle(d => d.endAngle)
              .padAngle(d => d.padAngle)
            )
            .attr("fill", d => {
              if (activeVehicleType === null) {
                return vehicleTypeColors(d.type);
              } else {
                return d.typeIndex === activeVehicleType ? vehicleTypeColors(d.type) : "#ddd";
              }
            })
            .style("opacity", d => {
              if (activeVehicleType === null) {
                return 1;
              } else {
                return d.typeIndex === activeVehicleType ? 1 : 0.3;
              }
            });

          segments.enter().append("path")
            .attr("d", d3.arc()
              .innerRadius(outerRadius + 6)
              .outerRadius(outerRadius + 20)
              .startAngle(d => d.startAngle)
              .endAngle(d => d.endAngle)
              .padAngle(d => d.padAngle)
            )
            .attr("fill", d => vehicleTypeColors(d.type))
            .attr("stroke", "#fff")
            .attr("stroke-width", 0.5)
            .style("opacity", 1)
            .on("mouseover", (event, d) => {
              tooltip.html(`<strong>${cameraLines[d.index]}</strong><br>${d.type}: ${d.value}`)
                .style("visibility", "visible");
              updateTooltipPosition(event);
            })
            .on("mousemove", (event) => {
              updateTooltipPosition(event);
            })
            .on("mouseout", () => tooltip.style("visibility", "hidden"))
            .on("click", (event, d) => {
              activeVehicleType = d.typeIndex;
              updateChords();
              updateOuterSegments();
            });

          segments.exit().remove();
        }

        updateOuterSegments();

        function updateChords() {
          currentMatrix = computeMatrix(activeVehicleType);
          chordsData = chordGenerator(currentMatrix);
          groupArcs.data(chordsData.groups)
            .transition().duration(300)
            .attr("d", arc);
          ribbons.data(chordsData)
            .transition().duration(300)
            .attr("d", ribbon)
            .attr("fill", d => color(cameraLines[d.source.index]));
        }
      },

      // 调用接口获取车流矩阵数据，并更新图表和表格
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
            this.processFlowMat();
            // 根据接口数据更新弦图，如果数据充足则渲染
            this.drawChordDiagram();
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

      // 将 3D 矩阵转换为二维矩阵（用于表格展示）
      processFlowMat() {
        let matrix = [];
        for (let i = 0; i < this.cameraLines.length; i++) {
          matrix[i] = [];
          for (let j = 0; j < this.cameraLines.length; j++) {
            let sum = 0;
            let details = [];
            for (let k = 0; k < this.labels.length; k++) {
              let val = parseFloat(this.flowmat[i][j][k]) || 0;
              details.push(val);
              sum += val;
            }
            matrix[i][j] = { sum, details };
          }
        }
        this.aggregatedMatrix = matrix;
        this.expandedRows = Array(this.cameraLines.length).fill(false);
      },

      toggleRowExpand(rowIndex) {
        this.$set(this.expandedRows, rowIndex, !this.expandedRows[rowIndex]);
      },

      handleFilter() {
        this.getFlowMatData();
      },

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

<style scoped>
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
</style>

<style>
  /* 针对 chord 图 tooltip 的样式 */
  .chord-tooltip {
    pointer-events: none;
    font-size: 12px;
    background: #fff;
    border: 1px solid #80cbc4;
    border-radius: 4px;
    padding: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    z-index: 9999;
    position: absolute;
    width: 200px;
  }
</style>
