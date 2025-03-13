<template>
  <div class="app-container">
    <!-- 筛选与操作区域 -->
    <div class="filter-container">
      <el-input v-model="listQuery.cameraName" clearable class="filter-item" style="width: 200px;" placeholder="请输入摄像头名称" />
      <el-button class="filter-item" type="primary" icon="el-icon-search" @click="handleFilter">
        搜索
      </el-button>
      <el-button class="filter-item" type="primary" icon="el-icon-plus" @click="handleCreate">
        添加摄像头
      </el-button>
      <el-button :loading="downloadLoading" class="filter-item" type="primary" icon="el-icon-download" @click="handleDownload">
        导出
      </el-button>
    </div>

    <!-- 摄像头列表 -->
    <el-table v-loading="listLoading" :data="list" border fit highlight-current-row>
      <el-table-column align="center" width="100px" label="摄像头ID" prop="cameraId" sortable />
      <el-table-column align="center" min-width="200px" label="摄像头名称" prop="cameraName" />
      <el-table-column align="center" min-width="300px" label="摄像头地址" prop="cameraURL" />
      <el-table-column align="center" min-width="200px" label="摄像头位置">
        <template slot-scope="scope">
          <span>{{ formatLocation(scope.row.cameraLocation) }}</span>
        </template>
      </el-table-column>
      <el-table-column align="center" label="操作" width="500" class-name="small-padding fixed-width">
        <template slot-scope="scope">
          <el-button type="primary" size="mini" @click="handleUpdate(scope.row)"> 编辑 </el-button>
          <el-button type="danger" size="mini" @click="handleDelete(scope.row)"> 删除 </el-button>
          <el-button type="warning" size="mini" @click="handleRules(scope.row)">规则配置</el-button>
          <el-button type="warning" size="mini" @click="handleLines(scope.row)">检测线配置</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <pagination v-show="total > 0" :total="total" :pageNum.sync="listQuery.pageNum" :pageSize.sync="listQuery.pageSize" @pagination="getList" />
    <!-- 添加/编辑摄像头对话框 -->
    <el-dialog :title="textMap[dialogStatus] + '摄像头'" :visible.sync="dialogFormVisible">
      <el-form ref="dataForm" :rules="rules" :model="dataForm" status-icon label-position="left" label-width="100px" style="width: 400px; margin-left:50px;">
        <el-form-item label="摄像头名称" prop="cameraName">
          <el-input v-model="dataForm.cameraName" />
        </el-form-item>
        <el-form-item label="摄像头地址" prop="cameraURL">
          <el-input v-model="dataForm.cameraURL" />
        </el-form-item>
        <el-form-item label="摄像头位置" prop="cameraLocation">
          <el-input v-model="dataForm.cameraLocation[0]" placeholder="经度" style="width:48%; margin-right:4%;" />
          <el-input v-model="dataForm.cameraLocation[1]" placeholder="纬度" style="width:48%;" />
        </el-form-item>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="dialogFormVisible = false">取消</el-button>
        <el-button v-if="dialogStatus === 'create'" type="primary" @click="createData">
          确定
        </el-button>
        <el-button v-else type="primary" @click="updateData">
          确定
        </el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { getCameraList, addCamera, updateCamera, deleteCamera } from '@/api/camera/camera'
import Pagination from '@/components/Pagination'

export default {
  name: 'CameraManagement',
  components: { Pagination },
  data() {
    return {
      list: [],
      total: 0,
      listLoading: true,
      listQuery: {
        pageNum: 1,
        pageSize: 20,
        cameraName: ''
      },
      dataForm: {
        cameraId: undefined,
        cameraName: '',
        cameraURL: '',
        cameraLocation: ['', '']
      },
      dialogFormVisible: false,
      dialogStatus: '',
      textMap: {
        update: '编辑',
        create: '创建'
      },
      rules: {
        cameraName: [{ required: true, message: '摄像头名称不能为空', trigger: 'blur' }],
        cameraURL: [{ required: true, message: '摄像头地址不能为空', trigger: 'blur' }],
        cameraLocation: [{type: 'array', required: true, message: '请填写经度和纬度', trigger: 'blur' }]
      },
      downloadLoading: false
    }
  },
  created() {
    this.getList()
  },
  methods: {
    getList() {
      this.listLoading = true
      const params = { ...this.listQuery }
      if (!params.cameraName) {
        delete params.cameraName
      }
      getCameraList(params)
        .then(response => {
          const data = response.data.data
          this.list = data.cameras || []
          this.total = data.total || 0
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
    resetForm() {
      this.dataForm = {
        cameraId: undefined,
        cameraName: '',
        cameraURL: '',
        cameraLocation: ['','']
      }
    },
    handleCreate() {
      this.resetForm()
      this.dialogStatus = 'create'
      this.dialogFormVisible = true
      this.$nextTick(() => {
        this.$refs.dataForm.clearValidate()
      })
    },
    createData() {
      this.$refs.dataForm.validate(valid => {
        if (valid) {
          addCamera(this.dataForm)
            .then(response => {
              const newCamera = response.data.data
              this.list.unshift(newCamera)
              this.dialogFormVisible = false
              this.$notify.success({
                title: '成功',
                message: '摄像头创建成功'
              })
            })
            .catch(response => {
              this.$notify.error({
                title: '失败',
                message: response.data.errmsg
              })
            })
        }
      })
    },
    handleUpdate(row) {
      // 拷贝数据到 dataForm
      this.dataForm = Object.assign({},{
        cameraId:row.cameraId,
        cameraName:row.cameraName,
        cameraLocation:row.cameraLocation
      })
      // 如果 cameraLocation 不是数组，则拆分成数组
      if (!Array.isArray(this.dataForm.cameraLocation)) {
        this.dataForm.cameraLocation = this.dataForm.cameraLocation.split(',')
      }
      this.dialogStatus = 'update'
      this.dialogFormVisible = true
      this.$nextTick(() => {
        this.$refs.dataForm.clearValidate()
      })
    },
    updateData() {
      console.log("update")
      this.$refs.dataForm.validate(valid => {
        if (valid) {
          updateCamera(this.dataForm)
            .then(() => {
              const index = this.list.findIndex(item => item.cameraId === this.dataForm.cameraId)
              if (index !== -1) {
                this.list.splice(index, 1, Object.assign({}, this.dataForm))
              }
              this.dialogFormVisible = false
              this.$notify.success({
                title: '成功',
                message: '摄像头更新成功'
              })
            })
            .catch(response => {
              this.$notify.error({
                title: '失败',
                message: response.data.errmsg
              })
            })
        }
      })
    },
    handleDelete(row) {
      this.$confirm('确定删除该摄像头吗？', '提示', { type: 'warning' })
        .then(() => {
          deleteCamera({cameraId:row.cameraId})
            .then(() => {
              this.$notify.success({
                title: '成功',
                message: '摄像头删除成功'
              })
              this.getList()
            })
            .catch(response => {
              this.$notify.error({
                title: '失败',
                message: response.data.errmsg
              })
            })
        })
        .catch(() => {})
    },
    handleDownload() {
      this.downloadLoading = true
      import('@/vendor/Export2Excel').then(excel => {
        const tHeader = ['摄像头ID', '摄像头名称', '摄像头地址', '摄像头位置']
        const filterVal = ['cameraId', 'cameraName', 'cameraURL', 'cameraLocation']
        excel.export_json_to_excel2(tHeader, this.list, filterVal, '摄像头信息')
        this.downloadLoading = false
      })
    },
    formatLocation(location) {
      if (Array.isArray(location)) {
        return location.join(', ')
      }
      return location
    },
    handleRules(camera) {
      this.$router.push({ path: '/cameraRules', query: { cameraId: camera.cameraId } })
    },
    handleLines(camera){
      this.$router.push({path:'/cameraLines', query: {cameraId:camera.cameraId}})
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
}
.filter-item {
  margin-right: 10px;
}
.small-padding {
  padding: 4px;
}
.fixed-width {
  width: 250px;
}
</style>
