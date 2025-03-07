<template>
  <div class="camera-management">
    <h2>摄像头管理页面</h2>
    <!-- 顶部操作按钮 -->
    <div style="margin-bottom: 20px;">
      <el-button type="primary" @click="openAddDialog">添加摄像头</el-button>
    </div>

    <!-- 摄像头列表区域 -->
    <section class="camera-list">
      <h3>摄像头列表</h3>
      <!-- 搜索框 -->
      <el-input
        v-model="searchKeyword"
        placeholder="输入名称搜索摄像头"
        clearable
        @clear="handleSearch"
        @input="handleSearch"
        style="width:300px; margin-bottom: 20px;">
      </el-input>

      <!-- 摄像头表格 -->
      <el-table :data="cameraList" border style="width: 100%">
        <el-table-column prop="cameraName" label="摄像头名称"></el-table-column>
        <el-table-column prop="cameraLiveStreamPreviewURL" label="预览地址"></el-table-column>
        <el-table-column label="位置">
          <template #default="scope">
            <span>{{ scope.row.cameraLocation.join(', ') }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160">
          <template #default="scope">
            <el-button type="primary" size="mini" @click="handleEdit(scope.row)">编辑</el-button>
            <el-button type="danger" size="mini" @click="handleDelete(scope.row.cameraId)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页（如果需要分页功能） -->
      <el-pagination
        background
        layout="prev, pager, next"
        :page-size="pageSize"
        :current-page="pageNum"
        :total="totalCameras"
        @current-change="handlePageChange"
        style="margin-top: 20px;">
      </el-pagination>
    </section>

    <!-- 添加摄像头弹窗 -->
    <el-dialog title="添加摄像头" :visible.sync="addDialogVisible">
      <el-form :model="newCamera" ref="addCameraForm" label-width="100px">
        <el-form-item label="摄像头名称">
          <el-input v-model="newCamera.cameraName" placeholder="请输入摄像头名称"></el-input>
        </el-form-item>
        <el-form-item label="摄像头地址">
          <el-input v-model="newCamera.cameraURL" placeholder="例如：rtsp://admin:password@ip:10554/udp/av0_0"></el-input>
        </el-form-item>
        <el-form-item label="摄像头位置">
          <el-input v-model="newCamera.cameraLocation[0]" placeholder="经度" style="width:48%; margin-right:4%"></el-input>
          <el-input v-model="newCamera.cameraLocation[1]" placeholder="纬度" style="width:48%"></el-input>
        </el-form-item>
      </el-form>
      <span slot="footer" class="dialog-footer">
        <el-button @click="addDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleAddCamera">确定</el-button>
      </span>
    </el-dialog>

    <!-- 编辑摄像头弹窗 -->
    <el-dialog title="编辑摄像头" :visible.sync="editDialogVisible">
      <el-form :model="editCamera" ref="editCameraForm" label-width="100px">
        <el-form-item label="摄像头名称">
          <el-input v-model="editCamera.cameraName" placeholder="请输入摄像头名称"></el-input>
        </el-form-item>
        <el-form-item label="摄像头地址">
          <el-input v-model="editCamera.cameraURL" placeholder="请输入摄像头地址"></el-input>
        </el-form-item>
        <el-form-item label="摄像头位置">
          <el-input v-model="editCamera.cameraLocation[0]" placeholder="经度" style="width:48%; margin-right:4%"></el-input>
          <el-input v-model="editCamera.cameraLocation[1]" placeholder="纬度" style="width:48%"></el-input>
        </el-form-item>
      </el-form>
      <span slot="footer" class="dialog-footer">
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleUpdateCamera">确定</el-button>
      </span>
    </el-dialog>
  </div>
</template>

<script>
import { getCameraList, deleteCamera, updateCamera, addCamera } from '@/api/camera/camera.js'

export default {
  name: 'cameraManagementView',
  data() {
    return {
      cameraList: [],
      totalCameras: 0,
      pageNum: 1,
      pageSize: 6,
      searchKeyword: '',
      // 新增摄像头弹窗状态
      addDialogVisible: false,
      // 新增摄像头的数据模型
      newCamera: {
        cameraName: '',
        cameraURL: '',
        cameraLocation: ['', '']
      },
      // 编辑摄像头弹窗状态
      editDialogVisible: false,
      // 编辑摄像头的数据模型
      editCamera: {
        cameraId: '',
        cameraName: '',
        cameraURL: '',
        cameraLocation: ['', '']
      }
    }
  },
  methods: {
    // 打开添加摄像头弹窗
    openAddDialog() {
      this.addDialogVisible = true
      // 重置表单数据
      this.newCamera = {
        cameraName: '',
        cameraURL: '',
        cameraLocation: ['', '']
      }
    },
    // 获取摄像头列表，同时传入分页及搜索参数
    fetchCameraList() {
      const params = {
        pageNum: this.pageNum,
        pageSize: this.pageSize
      }
      if(this.searchKeyword){
        params.cameraName=this.searchKeyword
      }
      getCameraList(params)
        .then(response => {
          response=response.data
          if(response.code === '200' || response.code === 200){
            this.cameraList = response.data.cameras || []
            this.totalCameras = response.data.cameraNum || 0
          } else {
            this.$message.error(response.msg || '获取摄像头列表失败')
          }
        })
        .catch(err => {
          console.error('获取摄像头列表异常', err)
          this.$message.error('获取摄像头列表异常')
        })
    },
    // 添加摄像头
    handleAddCamera() {
      addCamera(this.newCamera)
        .then(response => {
          response=response.data
          if(response.code === '200' || response.code === 200){
            this.$message.success('摄像头添加成功')
            this.addDialogVisible = false
            this.fetchCameraList()
          } else {
            this.$message.error(response.msg || '添加失败')
          }
        })
        .catch(err => {
          console.error('添加摄像头异常', err)
          this.$message.error('添加摄像头异常')
        })
    },
    // 打开编辑弹窗，并将数据填入表单
    handleEdit(camera) {
      this.editCamera = {
        cameraId: camera.cameraId,
        cameraName: camera.cameraName,
        cameraURL: camera.cameraURL,
        cameraLocation: Array.isArray(camera.cameraLocation)
          ? [...camera.cameraLocation]
          : camera.cameraLocation.split(',')
      }
      this.editDialogVisible = true
    },
    // 更新摄像头信息
    handleUpdateCamera() {
      updateCamera(this.editCamera)
        .then(response => {
          if(response.code === '200' || response.code === 200){
            this.$message.success('摄像头更新成功')
            this.editDialogVisible = false
            this.fetchCameraList()
          } else {
            this.$message.error(response.msg || '更新失败')
          }
        })
        .catch(err => {
          console.error('更新摄像头异常', err)
          this.$message.error('更新摄像头异常')
        })
    },
    // 删除摄像头
    handleDelete(cameraId) {
      this.$confirm('确定删除该摄像头吗？', '提示', {
        type: 'warning'
      }).then(() => {
        deleteCamera({ cameraId })
          .then(response => {
            if(response.code === '200' || response.code === 200){
              this.$message.success('摄像头删除成功')
              this.fetchCameraList()
            } else {
              this.$message.error(response.msg || '删除失败')
            }
          })
          .catch(err => {
            console.error('删除摄像头异常', err)
            this.$message.error('删除摄像头异常')
          })
      }).catch(() => {
        // 用户取消删除操作
      })
    },
    // 搜索及分页变化时更新列表
    handleSearch() {
      this.pageNum = 1
      this.fetchCameraList()
    },
    handlePageChange(newPage) {
      this.pageNum = newPage
      this.fetchCameraList()
    }
  },
  mounted() {
    this.fetchCameraList()
  }
}
</script>

<style scoped>
.camera-management {
  padding: 20px;
}
.camera-list {
  margin-top: 20px;
}
</style>
