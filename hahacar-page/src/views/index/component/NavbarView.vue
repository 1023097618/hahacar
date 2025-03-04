<template>
  <div class="navbar" style="display: flex; justify-content: flex-end">
    <el-header>
      <el-select :value="styleValue" placeholder="请选择" @change="selectStyle" select="mini">
        <el-option v-for="item in styles" :key="item.value" :label="item.label" :value="item.value">
          <i :class="item.icon"></i>
          <span>{{ item.label }}</span>
        </el-option>
      </el-select>
    </el-header>
  </div>
</template>

<script>
  import { styleChange } from '@/api/user/user.js'
  export default {
    name: 'AppMain',
    data() {
      return {
        styles: [
          {
            "label": "浅色",
            "value": 1,
            "icon":"fas fa-sun"
          }, {
            "label": "深色",
            "value": 2,
            "icon":"fas fa-moon"
          },
          {
            "label": "系统",
            "value": 3,
            "icon":"fas fa-gear"
          }
        ],
        mediaQuery: window.matchMedia('(prefers-color-scheme: dark)')
      }
    },
    computed: {
      styleValue(){
        return this.$store.getters.user.style
      }
    },
    methods: {
      selectStyle(newValue) {
        styleChange({ "style": newValue }).then(() => {
          this.$store.dispatch("UpdateUserTheme",newValue)
          this.updateTheme()
        }).catch(err => {
          console.log(err)
        })
      },
      updateTheme() {
        if (this.styleValue === 1) {
          //白天模式
          document.body.classList.remove("dark")
          document.body.classList.add("day")
        }
        if (this.styleValue === 2) {
          //黑夜模式
          document.body.classList.remove("day")
          document.body.classList.add("dark")
        }
        if (this.styleValue === 3) {
          // 跟随系统
          if (this.mediaQuery.matches) {
            document.body.classList.remove('day');
            document.body.classList.add('dark');
          } else {
            document.body.classList.remove('dark');
            document.body.classList.add('day');
          }
          // 监听系统主题变化
          this.mediaQuery.addEventListener('change', this.selectStyle);
        }
      }
    },
    created() {
      this.mediaQuery.addEventListener('change', this.selectStyle);
      this.updateTheme()
    },
    beforeDestroy() {
      this.mediaQuery.removeEventListener('change', this.selectStyle);
    }

  }
</script>

<style scoped>
  .el-dropdown-link {
    cursor: pointer;
    color: #409EFF;
  }

  .el-dropdown-link {
    height: 100%;
    display: inline-block;
    min-width: 100px;
  }

  .el-icon-arrow-down {
    font-size: 12px;
  }
  
  .el-select-dropdown__item{
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .el-select{
    width: 90px;
  }
</style>