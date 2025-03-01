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
	font-family: Raleway, sans-serif;
}

.day{
  
  --mainContent:#f5f5f9;

  --sideBarColor:#FFF;
  --sideBarTextColor:#303133;
  --sideBarSelectedTextColor:#409EFF;
  --sideBarSelectedColor:#ecf5ff;
  --sideBarHoverColor:#ecf5ff
}

.dark{
  --mainContent:#232333;;

  --sideBarColor:#191924;
  --sideBarTextColor:#fff;
  --sideBarSelectedTextColor:#fff;
  --sideBarSelectedColor:#4687ff;
  --sideBarHoverColor:rgb(34, 34, 45)
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