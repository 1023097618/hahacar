import Vue from 'vue'
import Router from 'vue-router'

Vue.use(Router)


const constantRoutes = [
  {
    path: '', name: 'indexView', component: () => import('@/views/index/indexView.vue'), hidden: false,meta:{title: '主页'}, children: [
      { path: '/vedio', name: 'vedioView', component: () => import('@/views/vedio/vedioView.vue'), hidden: false,meta:{title: '视频上传'} }
    ]
  },


]

const router = new Router({
  routes: constantRoutes
})

export function getCurrentRoute() {
  return constantRoutes
}
export default router
