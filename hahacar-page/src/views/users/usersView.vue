<template>
  <div class="app-container">
    <!-- 筛选与操作区域 -->
    <div class="filter-container">
      <el-input
        v-model="listQuery.username"
        clearable
        class="filter-item"
        style="width: 200px;"
        placeholder="请输入用户名"
      />
      <el-button class="filter-item" type="primary" icon="el-icon-search" @click="handleFilter">
        搜索
      </el-button>
      <el-button class="filter-item" type="primary" icon="el-icon-plus" @click="handleCreate">
        添加用户
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

    <!-- 用户列表 -->
    <el-table v-loading="listLoading" :data="list" border fit highlight-current-row>
      <el-table-column align="center" width="150px" label="用户名" prop="username" sortable />
      <el-table-column align="center" min-width="150px" label="真实姓名" prop="realName" />
      <el-table-column align="center" min-width="120px" label="用户权限">
        <template slot-scope="scope">
          <span v-if="scope.row.privilege === 1">普通用户</span>
          <span v-else-if="scope.row.privilege === 2">管理员用户</span>
          <span v-else>未知权限</span>
        </template>
      </el-table-column>
      <el-table-column align="center" min-width="150px" label="备注信息" prop="userRemark" />
      <el-table-column align="center" label="操作" width="250" class-name="small-padding fixed-width">
        <template slot-scope="scope">
          <el-button type="primary" size="mini" @click="handleUpdate(scope.row)">编辑</el-button>
          <el-button type="danger" size="mini" @click="handleDelete(scope.row)">删除</el-button>
          <el-button type="warning" size="mini" @click="handleViewCamera(scope.row)">摄像头权限</el-button>
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

    <!-- 添加/编辑用户对话框 -->
    <el-dialog :title="textMap[dialogStatus] + '用户'" :visible.sync="dialogFormVisible">
      <el-form
        ref="dataForm"
        :rules="rules"
        :model="dataForm"
        status-icon
        label-position="left"
        label-width="100px"
        style="width: 400px; margin-left:50px;"
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="dataForm.username" />
        </el-form-item>
        <el-form-item label="真实姓名" prop="realName">
          <el-input v-model="dataForm.realName" />
        </el-form-item>
        <el-form-item label="用户权限" prop="privilege">
          <el-select v-model="dataForm.privilege" placeholder="请选择用户权限">
            <el-option label="普通用户" :value="1"></el-option>
            <el-option label="管理员用户" :value="2"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="备注信息" prop="userRemark">
          <el-input
            v-model="dataForm.userRemark"
            type="textarea"
            :autosize="{ minRows: 2, maxRows: 4 }"
          />
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
    <user-camera :visible.sync="userCameraVisible" ref="userCamera" />
  </div>
</template>

<script>
import { getUsers, addUser, updateUser, deleteUser } from '@/api/user/user.js'
import Pagination from '@/components/Pagination'
import UserCamera from './components/userCamera.vue'

export default {
  name: 'UserManagement',
  components: { Pagination,UserCamera },
  data() {
    return {
      list: [],
      total: 0,
      listLoading: true,
      listQuery: {
        pageNum: 1,
        pageSize: 10,
        username: ''
      },
      dataForm: {
        userId: undefined,
        username: '',
        realName: '',
        privilege: 1,
        userRemark: ''
      },
      dialogFormVisible: false,
      dialogStatus: '',
      textMap: {
        update: '编辑',
        create: '创建'
      },
      rules: {
        username: [{ required: true, message: '用户名不能为空', trigger: 'blur' }],
        realName: [{ required: true, message: '真实姓名不能为空', trigger: 'blur' }],
        privilege: [{ required: true, message: '请选择用户权限', trigger: 'change' }]
      },
      downloadLoading: false,
      userCameraVisible:false
    }
  },
  created() {
    this.getList()
  },
  methods: {
    getList() {
      this.listLoading = true
      const params = { ...this.listQuery }
      if (!params.username) {
        delete params.username
      }
      getUsers(params)
        .then(response => {
          const data = response.data.data
          this.list = data.users || []
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
        userId: undefined,
        username: '',
        realName: '',
        privilege: 1,
        userRemark: ''
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
          addUser(this.dataForm)
            .then(response => {
              const newUser = response.data.data
              this.list.unshift(newUser)
              this.dialogFormVisible = false
              this.$notify.success({
                title: '成功',
                message: '用户创建成功'
              })
              this.getList()
            })
            .catch(response => {
              this.$notify.error({
                title: '失败',
                message: response.data.errmsg || '用户创建失败'
              })
            })
        }
      })
    },
    handleUpdate(row) {
      // 将选中行数据复制到表单
      this.dataForm = Object.assign({}, {
        userId: row.userId || '',
        username: row.username || '',
        realName: row.realName || '',
        privilege: row.privilege || '',
        userRemark: row.userRemark || ''
      })
      this.dialogStatus = 'update'
      this.dialogFormVisible = true
      this.$nextTick(() => {
        this.$refs.dataForm.clearValidate()
      })
    },
    updateData() {
      this.$refs.dataForm.validate(valid => {
        if (valid) {
          updateUser(this.dataForm)
            .then(() => {
              const index = this.list.findIndex(item => item.userId === this.dataForm.userId)
              if (index !== -1) {
                this.list.splice(index, 1, Object.assign({}, this.dataForm))
              }
              this.dialogFormVisible = false
              this.$notify.success({
                title: '成功',
                message: '用户更新成功'
              })
              this.getList()
            })
            .catch(response => {
              this.$notify.error({
                title: '失败',
                message: response.data.errmsg || '用户更新失败'
              })
            })
        }
      })
    },
    handleDelete(row) {
      this.$confirm('确定删除该用户吗？', '提示', { type: 'warning' })
        .then(() => {
          deleteUser({ userId: row.userId })
            .then(() => {
              this.$notify.success({
                title: '成功',
                message: '用户删除成功'
              })
              this.getList()
            })
            .catch(response => {
              this.$notify.error({
                title: '失败',
                message: response.data.errmsg || '用户删除失败'
              })
            })
        })
        .catch(() => {})
    },
    handleDownload() {
      this.downloadLoading = true
      import('@/vendor/Export2Excel').then(excel => {
        const tHeader = ['用户名', '真实姓名', '用户权限', '备注信息']
        const filterVal = ['username', 'realName', 'privilege', 'userRemark']
        excel.export_json_to_excel2(tHeader, this.list, filterVal, '用户信息')
        this.downloadLoading = false
      })
    },
    handleViewCamera(row) {
      // 调用 UserCamera 弹窗，并传入当前用户ID
      this.$refs.userCamera.openDialog(row.userId)
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
