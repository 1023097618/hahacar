import Vue from 'vue'
import Router from 'vue-router'

Vue.use(Router)




const constantRoutes = [
  { path: '/login', name: 'loginView', component: () => import('@/views/login/LoginView.vue'), hidden: true },
  { path: '/resetPasswordByOldPassword', name: 'resetPasswordByOldPasswordView', component: () => import('@/views/login/resetPasswordByOldPasswordView.vue'), hidden: true },
  { path: '/dev', name: 'devView', component: () => import('@/views/dev/devView.vue'), hidden: false,meta:{title: '实验页面'}}
]

const userRoutes = [
  {
    path: '', name: 'indexView', component: () => import('@/views/index/indexView.vue'), hidden: false,meta:{title: '主页'}, children: [
      { path: '/map', name: 'mapView', component: () => import('@/views/map/mapView.vue'), hidden: false,meta:{title: '地图中心',icon:'icon-map'} },
      { path: '/data', name: 'dataView', component: () => import('@/views/data/dataView.vue'), hidden: false,meta:{title: '数据中心',icon:'icon-data'} },
      { path: '/vedio', name: 'vedioView', component: () => import('@/views/upload/uploadView.vue'), hidden: false,meta:{title: '在线识别',icon:'icon-find-car'} }
      // { path: '/dev', name: 'devView', component: () => import('@/views/dev/devView.vue'), hidden: false,meta:{title: '实验页面'}}
    ],
  },{path: '', name: 'subPageView', component: () => import('@/views/index/subPageView.vue'), hidden: true,meta:{title: '二级页面'}, children: [
    { path: '/categoryDetail', name: 'categoryDetailView', component: () => import('@/views/data/subpages/categoryDetailView.vue'), hidden: true,meta:{title: '车辆类型分布数据'}},
    { path: '/flowDetail', name: 'flowDetailView', component: () => import('@/views/data/subpages/flowDetailView.vue'), hidden: true,meta:{title: '车流量数据'}},
    { path:'/chordDetail',name:'chordDetailView',component:()=>import('@/views/data/subpages/chordDetailView.vue'), hidden: true,meta:{title: '车流量和弦图'}},
    { path: '/holdDetail', name: 'holdDetailView', component: () => import('@/views/data/subpages/holdDetailView.vue'), hidden: true,meta:{title: '拥挤程度数据'}},
    { path: '/alertDetail', name: 'alertDetailView', component: () => import('@/views/data/subpages/alertDetailView.vue'), hidden: true,meta:{title: '预警数量数据'}},
    { path: '/cameraList', name: 'cameraListView', component: () => import('@/views/map/subpages/cameraList.vue'), hidden: true,meta:{title: '摄像头列表'}},
    { path:'/alertList',name:'alertListView',component:()=>import('@/views/map/subpages/alertList.vue'), hidden: true,meta:{title: '预警信息列表'}},
    { path:'/cameraLines',name:'cameraLineListView',component:()=>import('@/views/camera/subpages/cameraLines.vue'), hidden: true,meta:{title: '摄像头碰撞线设置列表'}}
  ]},
  { path: '/resetPasswordByToken', name: 'resetPasswordByTokenView', component: () => import('@/views/login/resetPasswordByTokenView.vue'), hidden: true },

]

const rootRoutes=[
  {
    path: '', name: 'indexView', component: () => import('@/views/index/indexView.vue'), hidden: false,meta:{title: '主页'}, children: [
      { path: '/map', name: 'mapView', component: () => import('@/views/map/mapView.vue'), hidden: false,meta:{title: '地图中心',icon:'icon-map'} },
      { path: '/data', name: 'dataView', component: () => import('@/views/data/dataView.vue'), hidden: false,meta:{title: '数据中心',icon:'icon-data'} },
      { path: '/vedio', name: 'vedioView', component: () => import('@/views/upload/uploadView.vue'), hidden: false,meta:{title: '在线识别',icon:'icon-find-car'} },
      { path: '/users', name: 'usrsView', component: () => import('@/views/users/usersView.vue'), hidden: false,meta:{title: '用户管理',icon:'icon-user'} },
      { path: '/camera', name: 'cameraManagementView', component: () => import('@/views/camera/cameraManagement.vue'), hidden: false,meta:{title: '摄像头管理',icon:'icon-camera_add_fill'} },
      // { path: '/dev', name: 'devView', component: () => import('@/views/dev/devView.vue'), hidden: false,meta:{title: '实验页面'}}
    ],
  },{path: '', name: 'subPageView', component: () => import('@/views/index/subPageView.vue'), hidden: true,meta:{title: '二级页面'}, children: [
    { path: '/categoryDetail', name: 'categoryDetailView', component: () => import('@/views/data/subpages/categoryDetailView.vue'), hidden: true,meta:{title: '车辆类型分布数据'}},
    { path: '/flowDetail', name: 'flowDetailView', component: () => import('@/views/data/subpages/flowDetailView.vue'), hidden: true,meta:{title: '车流量数据'}},
    { path:'/chordDetail',name:'chordDetailView',component:()=>import('@/views/data/subpages/chordDetailView.vue'), hidden: true,meta:{title: '车流量和弦图'}},
    { path: '/holdDetail', name: 'holdDetailView', component: () => import('@/views/data/subpages/holdDetailView.vue'), hidden: true,meta:{title: '拥挤程度数据'}},
    { path: '/alertDetail', name: 'alertDetailView', component: () => import('@/views/data/subpages/alertDetailView.vue'), hidden: true,meta:{title: '预警数量数据'}},
    { path: '/cameraList', name: 'cameraListView', component: () => import('@/views/map/subpages/cameraList.vue'), hidden: true,meta:{title: '摄像头列表'}},
    { path: '/cameraRules', name: 'cameraRulesView', component: () => import('@/views/camera/subpages/cameraRules.vue'), hidden: true,meta:{title: '摄像头规则配置'}},
    { path:'/alertList',name:'alertListView',component:()=>import('@/views/map/subpages/alertList.vue'), hidden: true,meta:{title: '预警信息列表'}},
    { path:'/cameraLines',name:'cameraLineListView',component:()=>import('@/views/camera/subpages/cameraLines.vue'), hidden: true,meta:{title: '摄像头碰撞线设置列表'}},
  ]},
  { path: '/resetPasswordByToken', name: 'resetPasswordByTokenView', component: () => import('@/views/login/resetPasswordByTokenView.vue'), hidden: true },


]

function createRoute() {
  return new Router({
    mode:'hash',
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
