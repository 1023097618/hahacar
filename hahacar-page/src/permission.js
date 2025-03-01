import router from "./router"
import store from "./store"
import { GetCookie,RemoveCookie } from "./utils/auth"

const whiteList=['/login','/resetPasswordByOldPassword']
router.beforeEach((to,from,next)=>{
    const token=GetCookie()
    if(token){
        if(store.getters.permmited===0){
            store.dispatch("GetUserInfoAction", token).then(() => {
                //授权为真
                if(store.getters.user.firstLogin===1){
                    //授权为真但首次登录
                    next("/resetPasswordByToken")
                }else{
                    //授权为真且非首次登录
                    if(to.path !== '/login' && to.path!== '/resetPasswordByToken'){
                        next(to.path)
                    }else{
                        next('/')
                    }
                }
            }).catch((err) => {
                //授权为假
                console.log(err)
                RemoveCookie()
                next('/login')
            })
        }else{
            //授权过了
            if(store.getters.user.firstLogin===1){
                //授权过但首次登录
                if(to.path!=="/resetPasswordByToken"){
                    next("/resetPasswordByToken")
                }else{
                    next()
                }
            }else{
                //授权过但非首次登录
                if(to.path !== '/login' && to.path!== '/resetPasswordByToken'){
                    next()
                }else{
                    next('/')
                }
            }

        }
    }else{
        //没有token，只允许访问白名单上的网站
        if(whiteList.indexOf(to.path)>=0){
            next()
        }else{
            if(from.path!=='/login'){
                next('/login')
            }else{
                next(false)
            }
        }
    }
})