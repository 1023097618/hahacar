<template>
    <el-dialog
      title="添加用户"
      :visible="this.visible"
      width="90%"
      :before-close="closeDialog"
      center
      style="overflow: hidden"
      top="3vh"
      :close-on-click-modal="false"
    >
      <div style="overflow-y: auto; height: 70vh">
        <el-form :model="user" label-position="right" label-width="80px">
          <el-form-item label="用户名">
            <el-input v-model="user.username"></el-input>
          </el-form-item>
          <el-form-item label="真实姓名">
            <el-input v-model="user.realName"></el-input>
          </el-form-item>
          <el-form-item label="备注信息">
            <el-input v-model="user.userRemark"
            type="textarea"
            :autosize="{ minRows: 2, maxRows: 4}"></el-input>
          </el-form-item>
        </el-form>
      </div>
      <span slot="footer" class="dialog-footer">
        <el-button @click="closeDialog()">取 消</el-button>
        <el-button type="primary" :loading="loading" @click="sureDialog()">确 定</el-button>
      </span>
    </el-dialog>
  </template>
  
  <script>
  import { addUser } from '@/api/user/user.js'
  
  export default {
    name: 'UserAdd',
    data() {
      return {
        user: {
          username: '',
          realName: '',
          userRemark: ''
        },
        loading: false // 添加加载状态
      };
    },
    props: {
      visible: {
        type: Boolean,
        required: true
      }
    },
    methods: {
      openDialog(user) {
        this.user=user
        this.$emit('update:visible', true)
      },
      closeDialog() {
        this.$emit('update:visible', false)
        this.user = {
          username: '',
          realName: '',
          userRemark: ''
        }
      },
      sureDialog() {
        this.loading = true // 开启加载状态
        addUser({
          username: this.user.username,
          realName: this.user.realName,
          userRemark: this.user.userRemark
        })
          .then(res => {
            this.$emit('updateGoods')
            console.log(res)
            this.closeDialog() // 关闭弹窗
          })
          .catch(err => {
            this.$message({
              type:'error',
              message:'添加用户失败'
            })
            console.log(err)
          })
          .finally(() => {
            this.loading = false // 关闭加载状态
          })
      }
    }
  };
  </script>
  