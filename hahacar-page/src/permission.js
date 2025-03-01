import router from "./router"
import store from "./store"
import { GetCookie,RemoveCookie } from "./utils/auth"

const whiteList=['/login','/register']
router.beforeEach((to,from,next)=>{
    const token=GetCookie()
    if(token){
        if(store.getters.permmited===0){
            store.dispatch("GetUserInfoAction", token).then(() => {
                //授权为真
                if(to.path !== '/login'){
                    next(to.path)
                }else{
                    next('/dashboard')
                }
            }).catch((err) => {
                //授权为假
                console.log(err)
                RemoveCookie()
                next('/login')
            })
        }else{
            //授权过了
            if(to.path !== '/login'){
                next()
            }else{
                next('/dashboard')
            }
        }
    }else{
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