const getters={
    token: state=>state.user.token,
    permmited: state=>state.user.permitted,
    username: state=>state.user.user.username,
    //这边应该是permittedRoutes，早期命名不规范的坑
    permittedRoutes: state=>state.user.permittedroutes,
    user:state=>state.user.user,
    tasks:state=>state.socket.tasks,
    sid:state=>state.socket.sid,
    alertMessages:state=>state.socket.alertMessages,
    cameraSituations:state=>state.socket.cameraSituations
}
export default getters