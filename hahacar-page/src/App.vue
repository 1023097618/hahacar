<template>
  <div id="app"  >
    <router-view/>
  </div>
</template>

<style>
  * {
	box-sizing: border-box;
	margin: 0;
	padding: 0;
  
}
h2,h3{
  color: var(--textColor);
}

.el-table__cell{
  background-color: var(--mainContent) !important
}
.el-table th.el-table__cell{
  background-color: var(--mainContent) !important
}
.el-table{
  background-color: var(--mainContent) !important
}
.el-table td.el-table__cell, .el-table th.el-table__cell.is-leaf{
  border-bottom: 0px !important
}
.hover-row td{
  background-color: var(--sideBarHoverColor) !important
}

.el-header {
    background-color: #4687ff!important;
    color: #333;
    line-height: 56px!important;
    height: 56px!important;
  }

  .pagination-container{
    background-color: var(--paginationBg) !important
  }
  .el-input__inner{
    background-color: var(--inputBg) !important
  }

  .el-dialog{
    background-color: var(--tooltipBg) !important;
  }

  .el-card{
    background-color: var(--sideBarColor) !important;
  }

  
.day{
  
  --mainContent:#f5f5f9;

  --sideBarColor:#FFF;
  --sideBarTextColor:#303133;
  --sideBarSelectedTextColor:#409EFF;
  --sideBarSelectedColor:#ecf5ff;
  --sideBarHoverColor:#ecf5ff;

  --textColor:#566a7f;

  --paginationBg: #e8e8e8;
  --inputBg: #ffffff;
  --tooltipBg: #ffffff;
}

.dark{
  --mainContent:#232333;;

  --sideBarColor:#191924;
  --sideBarTextColor:#fff;
  --sideBarSelectedTextColor:#fff;
  --sideBarSelectedColor:#4687ff;
  --sideBarHoverColor:rgb(34, 34, 45);

  --textColor:#cbcbe2;

  --paginationBg: #2a2a36;
  --inputBg: #2b2b3a;
  --tooltipBg: #2b2b3a;
}


/* #app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
}

nav {
  padding: 30px;
}

nav a {
  font-weight: bold;
  color: #2c3e50;
}

nav a.router-link-exact-active {
  color: #42b983;
} */
</style>
<script>
  export default {
    name:'App',
    mounted(){
      //默认白天样式
      document.body.className="day"
    }
  }
</script>