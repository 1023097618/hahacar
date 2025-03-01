<template>
  <div class="navbar" style="display: flex; justify-content: space-between;">
    <el-header>右半边还需要美化，我知道和左半边的颜色有点不搭</el-header>
  </div>
</template>

<script>
  export default {
    name: 'AppMain',
    data() {
      return {
        
      }
    },
    computed: {
      key() {
        return this.$route.fullPath
      }
    },
    methods: {
    },
    created(){
    }
  }
</script>

<style scoped>
  .el-dropdown-link {
    cursor: pointer;
    color: #409EFF;
  }
  .el-dropdown-link{
    height: 100%;
    display: inline-block;
    min-width: 100px;
  }
  .el-icon-arrow-down {
    font-size: 12px;
  }
</style>