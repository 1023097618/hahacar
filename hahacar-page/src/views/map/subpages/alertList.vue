<template>
  <div class="app-container">
    <!-- 筛选与操作区域 -->
    <div class="filter-container">
      <el-input
        v-model="listQuery.alertId"
        clearable
        class="filter-item"
        style="width: 200px;"
        placeholder="请输入预警ID"
      />
      <!-- 摄像头下拉多选 -->
      <el-select
        v-model="listQuery.cameraIds"
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
      <el-select
        v-model="listQuery.alertType"
        clearable
        multiple
        class="filter-item"
        placeholder="预警状态"
        style="width: 150px;"
      >
        <el-option label="正在发生" :value="'1'" />
        <el-option label="已经发生" :value="'2'" />
        <el-option label="已经结束" :value="'3'" />
      </el-select>
      <el-date-picker
        v-model="listQuery.alertStartTimeFrom"
        type="datetime"
        placeholder="预警开始时间（起）"
        class="filter-item"
        style="width: 200px;"
        format="yyyy-MM-dd HH:mm:ss"
        value-format="yyyy-MM-dd HH:mm:ss"
      />
      <el-date-picker
        v-model="listQuery.alertStartTimeTo"
        type="datetime"
        placeholder="预警开始时间（止）"
        class="filter-item"
        style="width: 200px;"
        format="yyyy-MM-dd HH:mm:ss"
        value-format="yyyy-MM-dd HH:mm:ss"
      />
      <el-button class="filter-item" type="primary" icon="el-icon-search" @click="handleFilter">
        搜索
      </el-button>
      <el-button
        :loading="downloadLoading"
        class="filter-item"
        type="primary"
        icon="el-icon-download"
        @click="handleDownload"
      >
        导出
      </el-button>
    </div>

    <!-- 预警消息列表 -->
    <el-table v-loading="listLoading" :data="list" border fit highlight-current-row>
      <el-table-column align="center" width="100px" label="预警ID" prop="alertId" sortable />
      <el-table-column align="center" min-width="150px" label="摄像头名称" prop="cameraName" />
      <el-table-column
        align="center"
        min-width="100px"
        label="预警状态"
        :formatter="formatAlertType"
        prop="alertType"
      />
      <el-table-column
        align="center"
        min-width="200px"
        label="预警开始时间"
        prop="alertStartTime"
        :formatter="formatTime"
      />
      <el-table-column
        align="center"
        min-width="200px"
        label="预警结束时间"
        prop="alertEndTime"
        :formatter="formatTime"
      />
      <el-table-column
        align="center"
        min-width="200px"
        label="处理时间"
        prop="alertProcessedTime"
        :formatter="formatTime"
      />
      <el-table-column
        align="center"
        min-width="150px"
        :formatter="formatruleType"
        label="触发规则"
        prop="ruleType"
      />
      <el-table-column align="center" min-width="250px" label="备注" prop="ruleRemark" />
      <!-- 新增预警图片列 -->
      <el-table-column align="center" min-width="150px" label="预警图片">
        <template slot-scope="scope">
          <el-image
            v-if="scope.row.alertImage"
            style="width: 100px; height: 100px"
            :src="GetImageURL(scope.row.alertImage)"
            fit="cover"
            :preview-src-list="[GetImageURL(scope.row.alertImage)]"
          ></el-image>
          <span v-else>无</span>
        </template>
      </el-table-column>
      <el-table-column align="center" label="操作" width="150" class-name="small-padding fixed-width">
        <template slot-scope="scope">
          <!-- 当预警状态不为 '已经结束' 时，可进行处理 -->
          <el-button
            v-if="scope.row.alertType !== '3'"
            type="primary"
            size="mini"
            @click="handleProcess(scope.row)"
          >
            处理
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <pagination
      v-show="total > 0"
      :total="total"
      :pageNum.sync="listQuery.pageNum"
      :pageSize.sync="listQuery.pageSize"
      @pagination="getList"
    />
  </div>
</template>

<script>
import { getAlerts, processAlert } from '@/api/alert/alert.js'
import {getImageURL} from '@/api/storage/storage.js'
import { getCameraList } from '@/api/camera/camera'
import Pagination from '@/components/Pagination'
export default {
  name: 'alertListView',
  components: { Pagination },
  data() {
    return {
      list: [],
      total: 0,
      listLoading: true,
      downloadLoading: false,
      listQuery: {
        pageNum: 1,
        pageSize: 20,
        alertId: '',
        // 将摄像头名称输入框替换为摄像头id的多选数组
        cameraIds: [],
        alertType: [],
        alertStartTimeFrom: '',
        alertStartTimeTo: ''
      },
      cameraOptions: [] // 用于下拉框选项
    }
  },
  created() {
    // 如果路由参数中存在 alertType，则赋值给 listQuery
    if (this.$route.query.alertType) {
      this.listQuery.alertType = Array.isArray(this.$route.query.alertType)
        ? this.$route.query.alertType
        : [this.$route.query.alertType]
    }
    this.getList()
    this.getCameraOptions()
  },
  methods: {
    getList() {
      this.listLoading = true
      // 拷贝参数并去除空值和空数组
      const params = { ...this.listQuery }
      Object.keys(params).forEach(key => {
        if (Array.isArray(params[key]) && params[key].length === 0) {
          delete params[key]
        } else if (!params[key] && typeof params[key] !== 'number') {
          delete params[key]
        }
      })
      getAlerts(params)
        .then(response => {
          const data = response.data.data
          this.list = data.alerts || []
          this.total = parseInt(data.alertNum) || 0
          this.listLoading = false
        })
        .catch(() => {
          this.list = []
          this.total = 0
          this.listLoading = false
        })
    },
    handleFilter() {
      this.listQuery.pageNum = 1
      this.getList()
    },
    formatAlertType(row, column, cellValue) {
      switch (cellValue) {
        case '1':
          return '正在发生'
        case '2':
          return '已经发生'
        case '3':
          return '已经结束'
        default:
          return cellValue
      }
    },
    formatruleType(row, column, cellValue) {
      switch (cellValue) {
        case '1':
          return '检测到违规车辆'
        case '2':
          return '车辆拥堵'
        case '3':
          return '车流量大'
        default:
          return cellValue
      }
    },
    formatTime(row, column, cellValue) {
      if (cellValue === null || cellValue === 'null' || cellValue === undefined || cellValue === '') {
        return '无'
      }
      return cellValue
    },
    handleProcess(row) {
      this.$confirm('确定要处理这条预警吗？', '提示', { type: 'warning' })
        .then(() => {
          processAlert({ alertId: row.alertId })
            .then(() => {
              this.$notify.success({
                title: '成功',
                message: '预警处理成功'
              })
              this.getList()
            })
            .catch(response => {
              this.$notify.error({
                title: '失败',
                message: response.data.errmsg || '处理预警失败'
              })
            })
        })
        .catch(() => {})
    },
    handleDownload() {
      this.downloadLoading = true
      import('@/vendor/Export2Excel').then(excel => {
        const tHeader = [
          '预警ID',
          '摄像头名称',
          '预警状态',
          '预警开始时间',
          '预警结束时间',
          '处理时间',
          '触发规则',
          '备注'
        ]
        const filterVal = [
          'alertId',
          'cameraName',
          'alertType',
          'alertStartTime',
          'alertEndTime',
          'alertProcessedTime',
          'ruleType',
          'ruleRemark'
        ]
        const listForExport = this.list.map(item => {
          return {
            ...item,
            alertType: this.formatAlertType(null, null, item.alertType)
          }
        })
        excel.export_json_to_excel2(tHeader, listForExport, filterVal, '预警信息')
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
    GetImageURL(fileName){
      const result=getImageURL(fileName)
      return result
    }
  }
}
</script>

<style scoped>
.app-container {
  padding: 20px;
}
.filter-container {
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
}
.filter-item {
  margin-right: 10px;
  margin-bottom: 10px;
}
.small-padding {
  padding: 4px;
}
.fixed-width {
  width: 150px;
}
</style>
