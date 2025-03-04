import Vue from 'vue'
import App from './App.vue'
import router from './router'
import store from './store'
import './permission'
import ElementUI from 'element-ui'
import('element-ui/lib/theme-chalk/index.css');
import '@fortawesome/fontawesome-free/css/all.min.css';
import socket from '@/utils/socket'

//伪造后端请求(调试用)
// import './mock'
Vue.use(ElementUI)
Vue.prototype.$socket=socket

Vue.config.productionTip = false

new Vue({
  router,
  store,
  render: h => h(App)
}).$mount('#app')
