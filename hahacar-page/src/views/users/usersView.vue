<template>
  <div id="users">
    <webErrorResult :error="weberror"></webErrorResult>
    <el-skeleton :rows="3" animated :loading="isload" />
    <el-table :data="users" style="width: 100;" :height="tableConfig.height" :row-class-name="tableRowClassName" :key="updatekey"
      v-if="!isload && !weberror">
      <el-table-column prop="username" label="用户名" width="150">
      </el-table-column>
      <el-table-column prop="realName" label="真实姓名" width="150">
      </el-table-column>
      <el-table-column label="用户权限" width="120">
        <template slot-scope="scope">
          <span v-if="scope.row.privilege === 1">普通用户</span>
          <span v-else-if="scope.row.privilege === 2">管理员用户</span>
          <span v-else>未知权限</span>
        </template>
      </el-table-column>
      <el-table-column prop="userMark" label="备注信息" width="120">
      </el-table-column>
      <el-table-column label="摄像头权限查看" width="120">
        <template slot-scope="scope">
          <el-button @click.native.prevent="ViewUserCamera(scope.row)" type="primary" icon="el-icon-view" size="mini">
          </el-button>
        </template>
      </el-table-column>
      <el-table-column fixed="right" width="210">
        <template slot="header">
          <div style="display: flex; justify-content: center;">
            <el-button size="mini" type="primary" icon="el-icon-plus" @click="AddUser()"></el-button>
          </div>
        </template>
        <template slot-scope="scope">
          <div style="display: flex; justify-content: center;">
            <el-button @click.native.prevent="EditUser(scope.row)" type="primary" icon="el-icon-edit" size="mini">
            </el-button>
            <el-button @click.native.prevent="handleDeleteUser(scope.row.userId)" type="danger" icon="el-icon-delete"
              size="mini">
            </el-button>
          </div>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination :current-page="currentPage" :page-size="pageSize" layout="prev, pager, next" :total="userNum" background
      @current-change="handlePageChange" v-if="userNum > pageSize">
    </el-pagination>
    <UserAdd :visible.sync="UserAddVisible" @updateGoods="GetUsers" ref="userAdd" />
    <UserCamera :visible.sync="UserCameraVisible" ref="userCamera" />
    <UserEdit :visible.sync="UserEditVisible" ref="userEdit"/>
  </div>
</template>

<script>
  import { getUsers,deleteUser } from '@/api/user/user.js'
  import UserAdd from './components/userAdd.vue'
  import UserCamera from './components/userCamera.vue'
  import webErrorResult from '@/components/webErrorResult.vue'
  import UserEdit from './components/userEdit'
  export default {
    name: 'usersView',
    methods: {
      handlePageChange(page) {
        this.currentPage = page
        this.GetUsers()
      },
      handleDeleteUser(userId) {
        this.$confirm('确定要删除该用户吗？', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }).then(() => {
          this.DeleteUser(userId)
        }).catch(() => {
          this.$message({
            type: 'info',
            message: '已取消删除'
          })
        })
      },
      DeleteUser(id) {
        deleteUser(id).then(
          res => {
            this.GetUsers()
            console.log(res)
          }
        ).catch(err => {
          console.log(err)
          this.$message({
            type: 'error',
            message: '删除失败'
          })
        })
      },
      GetUsers() {
        this.isload = true
        this.weberror=false
        getUsers(
          {
            pageNum: this.currentPage,
            pageSize: this.pageSize
          }
        ).then(res => {
          this.users = res.data.data.users
          this.userNum = res.data.data.totalGoods
          this.isload = false,
          this.weberror = false
          this.updatekey=!this.updatekey
        }).catch(err => {
          this.$message({
            type:'error',
            message:'获取用户信息失败'
          })
          this.isload = false,
          this.weberror = true
          console.log(err)
        })
      },
      EditUser(user) {
        this.$refs.userEdit.openDialog(user)
      },
      AddUser() {
        this.$refs.userAdd.openDialog()
      },
      ViewUserCamera(user) {
        this.$refs.userCamera.openDialog(user.userId)
      },
      //自适应表格高度  8(body边距)+60(navheader边距)+32(底部分页边距)
      getHeight() {
        this.tableConfig.height = window.innerHeight - 100
      },
      tableRowClassName({ row }) {
        if (row.privilege == 2) {
          //尊贵的管理员用户特效
          return 'warning-row'
        }
        return ''
      }
    },
    components: {
      UserAdd,
      webErrorResult,
      UserCamera,
      UserEdit
    }
    ,
    data() {
      return {
        users: [],
        UserAddVisible: false,
        UserCameraVisible: false,
        UserEditVisible:false,
        currentPage: 1,
        pageSize: 10,
        userNum: 0,
        tableConfig: {
          height: 200
        },
        isload: true,
        weberror: false,
        //表单没办法深度监听变量，所以需要一个updatekey来变化，每次update的时候都需要改变一下
        updatekey:false
      }
    },
    created() {
      this.GetUsers()
      this.getHeight()
      window.addEventListener('resize', this.getHeight)
    },
    destroyed() {
      window.removeEventListener('resize', this.getHeight)
    }
  }
</script>

<style>
  #users .el-table__body .cell {
    height: 100px;
  }

  #users .warning-row {
    background-color: rgb(253, 253, 206);
    ;
  }
</style>