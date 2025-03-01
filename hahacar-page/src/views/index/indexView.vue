<template>
  <div class="appwraper">
    <el-container>
      <el-aside width="260px" style="left: 0px;" class="sidebar-container">
        <SidebarView />
      </el-aside>
      <el-container>
        <el-header>
          <NavbarView />
        </el-header>
        <el-main :style="{ height: height + 'px' }">
          <AppMain />
        </el-main>
      </el-container>
    </el-container>
    <div class="main-container">
    </div>
  </div>
</template>

<style>
  .el-header {
    background-color: #4687ff!important;
    color: #333;
    line-height: 56px!important;
    height: 56px!important;
  }

  .el-aside {
    background-color: var(--sideBarColor);
    transition: border-color .3s,background-color .3s,color .3s;
  }

  .el-main {
    padding: 0px;
    background-color: var(--mainContent);
  }

  .el-menu-item{
    color: var(--sideBarTextColor);
    background-color: var(--sideBarColor);
  }

  .el-menu-item.is-active{
    color: var(--sideBarSelectedTextColor);
    background-color: var(--sideBarSelectedColor) !important;
  }
  .el-menu-item:hover{
    background-color: var(--sideBarHoverColor);
  }


</style>
<script>
  import SidebarView from './component/SidebarView.vue'
  import NavbarView from './component/NavbarView.vue'
  import AppMain from './component/AppMain.vue'
  export default {
    components: {
      SidebarView,
      NavbarView,
      AppMain
    },
    name: 'indexView',
    data() {
      return {
        height: 0
      }
    },
    methods: {
      //自适应表格高度  0(body边距)+60(navheader边距)
      getHeight() {
        this.height = window.innerHeight - 56
      }
    },
    created() {
      this.getHeight()
      window.addEventListener('resize', this.getHeight)
    }
    ,
    destroyed() {
      window.removeEventListener('resize', this.getHeight)
    },

  };
</script>