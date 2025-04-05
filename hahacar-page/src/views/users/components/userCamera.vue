<template>
  <el-dialog
    title="摄像头权限编辑页面"
    :visible="visible"
    width="90%"
    :before-close="closeDialog"
    center
    style="overflow: hidden"
    top="3vh"
    :close-on-click-modal="false">
    
    <!-- 搜索区域 -->
    <div style="margin-bottom: 20px;">
      <el-input
        v-model="searchText"
        placeholder="请输入摄像头名称"
        style="width: 200px;"
        @keyup.enter.native="handleSearch">
      </el-input>
      <el-button type="primary" @click="handleSearch">搜索</el-button>
    </div>

    <!-- 摄像头列表 -->
    <div style="overflow-y: auto; height: 50vh" id="userCameraPrivilege">
      <el-table
        ref="cameraTable"
        :data="cameraList"
        border
        style="width: 100%;"
        @selection-change="handleSelectionChange" v-loading="listLoading">
        <el-table-column type="selection" width="55"></el-table-column>
        <el-table-column prop="cameraName" label="摄像头名称"></el-table-column>
        <el-table-column
          prop="cameraLocation"
          label="位置"
          :formatter="formatLocation">
        </el-table-column>
        <el-table-column prop="cameraLiveStreamPreviewURL" label="预览地址"></el-table-column>
      </el-table>
    </div>
    <!-- 分页 -->
    <div style="margin-top: 20px; text-align: right;">
      <el-pagination
        background
        layout="prev, pager, next"
        :current-page="pageNum"
        :page-size="pageSize"
        :total="total"
        @current-change="handlePageChange">
      </el-pagination>
    </div>

    <!-- 底部操作按钮 -->
    <span slot="footer" class="dialog-footer">
      <el-button @click="closeDialog">取消</el-button>
      <el-button type="primary" @click="confirmDialog" :loading="loading">确定</el-button>
    </span>
  </el-dialog>
</template>

<script>
import { getUserCameraPrivilege, updateUserCameraPrivilege } from '@/api/user/user.js';
import { getCameraList } from '@/api/camera/camera.js';

export default {
  name: 'UserCamera',
  props: {
    visible: {
      type: Boolean,
      required: true
    }
  },
  data() {
    return {
      userId: null,               // 当前编辑的用户ID
      searchText: '',             // 搜索框输入的摄像头名称
      cameraList: [],             // 当前页的摄像头列表
      selectedCameraIds: [],      // 用户当前拥有权限的摄像头ID集合（跨页保存）
      pageNum: 1,                 // 当前页码
      pageSize: 20,               // 每页显示条数
      total: 0,                   // 摄像头总数
      loading: false,
      ignoreSelectionChange: false,
      listLoading:true //加载出来的数量，要等于2才能显示
    };
  },
  methods: {
    // 外部调用打开对话框，并传入需要编辑的用户ID
    openDialog(userId) {
      this.userId = userId;
      // 重置相关状态
      this.pageNum = 1;
      this.searchText = '';
      this.ignoreSelectionChange=true
      this.selectedCameraIds = [];
      this.listLoading=true
      // 加载该用户的摄像头权限和摄像头列表
      this.fetchUserPrivileges();
      this.$emit('update:visible', true);
    },
    // 关闭对话框
    closeDialog() {
      this.$emit('update:visible', false);
    },
    // 获取当前用户的摄像头权限
    fetchUserPrivileges() {
      getUserCameraPrivilege({ userId: this.userId })
        .then(response => {
          this.selectedCameraIds = response.data.data.cameras.map(cam => cam.cameraId);
          this.fetchCameraList();
        })
        .catch(err => {
          console.error(err);
          this.$message.error('获取用户摄像头权限失败');
        });
    },
    // 分页和搜索获取摄像头列表
    fetchCameraList() {
      let params = {
        pageNum: this.pageNum,
        pageSize: this.pageSize
      };
      if (this.searchText) {
        params.cameraName = this.searchText;
      }
      getCameraList(params)
        .then(response => {
          this.cameraList = response.data.data.cameras;
          this.total = response.data.data.total || 0;
          // 加载完成后，遍历当前页数据，将已选中的行选中
          this.$nextTick(() => {
            if (this.$refs.cameraTable) {
              this.cameraList.forEach(row => {
                if (this.selectedCameraIds.indexOf(row.cameraId) !== -1) {
                  this.$refs.cameraTable.toggleRowSelection(row, true);
                }
              });
            }
            this.ignoreSelectionChange=false
            this.listLoading=false
          });
        })
        .catch(err => {
          console.error(err);
          this.$message.error('获取摄像头列表失败');
        });
    },
    // 当表格的选中状态改变时，更新跨页的选中集合
    handleSelectionChange(selection) {
      if (this.ignoreSelectionChange) return;
      // 获取当前页所有摄像头ID
      const currentPageIds = this.cameraList.map(row => row.cameraId);
      // 先移除当前页中所有的摄像头ID（防止重复记录或取消选中）
      this.selectedCameraIds = this.selectedCameraIds.filter(id => !currentPageIds.includes(id));
      // 将当前页选中的摄像头ID加入集合
      selection.forEach(row => {
        if (this.selectedCameraIds.indexOf(row.cameraId) === -1) {
          this.selectedCameraIds.push(row.cameraId);
        }
      });
    },
    // 分页切换时重新加载数据
    handlePageChange(newPage) {
      this.pageNum = newPage;
      this.fetchCameraList();
    },
    // 搜索操作，重置页码后加载数据
    handleSearch() {
      this.pageNum = 1;
      this.fetchCameraList();
    },
    // 确认更新用户摄像头权限
    confirmDialog() {
      this.loading = true;
      updateUserCameraPrivilege({
        userId: this.userId,
        cameras: this.selectedCameraIds
      })
        .then(response => {
          // 根据接口返回的 code 判断成功与否
          if (response && response.data.code === '200') {
            this.$message.success('更新摄像头权限成功');
            this.closeDialog();
          } else {
            this.$message.error('更新摄像头权限失败');
          }
        })
        .catch(err => {
          console.error(err);
          this.$message.error('更新摄像头权限失败');
        })
        .finally(() => {
          this.loading = false;
        });
    },
    // 格式化摄像头位置（数组转成字符串展示）
    formatLocation(row, column, cellValue) {
      if (Array.isArray(cellValue)) {
        return cellValue.join(', ');
      }
      return cellValue;
    }
  }
};
</script>

<style>
#userCameraPrivilege .cell {
  height: 30px !important;
}
</style>
