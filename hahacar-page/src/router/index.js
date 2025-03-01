import Vue from 'vue'
import Router from 'vue-router'

Vue.use(Router)




const constantRoutes = [
  { path: '/login', name: 'loginView', component: () => import('@/views/login/LoginView.vue'), hidden: true }
]

const userRoutes = [
  {
    path: '', name: 'indexView', component: () => import('@/views/index/indexView.vue'), hidden: false,meta:{title: '主页'}, children: [
      { path: '/map', name: 'mapView', component: () => import('@/views/map/mapView.vue'), hidden: false,meta:{title: '地图中心'} },
      { path: '/data', name: 'dataView', component: () => import('@/views/data/dataView.vue'), hidden: false,meta:{title: '数据中心'} },
      { path: '/vedio', name: 'vedioView', component: () => import('@/views/upload/uploadView.vue'), hidden: false,meta:{title: '在线识别'} }
    ]
  }
]

const rootRoutes=[
  {
    path: '', name: 'indexView', component: () => import('@/views/index/indexView.vue'), hidden: false,meta:{title: '主页'}, children: [
      { path: '/map', name: 'mapView', component: () => import('@/views/map/mapView.vue'), hidden: false,meta:{title: '地图中心'} },
      { path: '/data', name: 'dataView', component: () => import('@/views/data/dataView.vue'), hidden: false,meta:{title: '数据中心'} },
      { path: '/vedio', name: 'vedioView', component: () => import('@/views/upload/uploadView.vue'), hidden: false,meta:{title: '在线识别'} }
    ]
  }
]

function createRoute() {
  return new Router({
    routes: constantRoutes
  })
}
const router = createRoute()

export function resetRouter() {
  const newrouter = createRoute()
  router.matcher = newrouter.matcher
}

export function addUserRoute(){
  userRoutes.forEach(route=>{
    router.addRoute(route)
  })
  return userRoutes
}

export function addRootRoute(){
  rootRoutes.forEach(route=>{
    router.addRoute(route)
  })
  return rootRoutes
}

export default router
