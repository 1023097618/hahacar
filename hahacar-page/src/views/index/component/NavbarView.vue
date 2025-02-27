<template>
  <div class="navbar" style="display: flex; justify-content: space-between;">
    <el-page-header content="hahacar" style="line-height: 60px;">
    </el-page-header>
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