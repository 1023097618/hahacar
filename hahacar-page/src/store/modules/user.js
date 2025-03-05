import { Login,GetUserInfo,changePasswordByOldpassword,changePasswordByToken } from "@/api/auth/login";
import {SetCookie,RemoveCookie} from "@/utils/auth";
import {addRootRoute,addUserRoute} from "@/router";
import router,{resetRouter} from "@/router";
export default {
    state:{
        token:'',
        //0代表没有授权  1代表普通用户  2代表管理员
        permitted:0,
        permittedroutes:[],
        user:{
            username:'',
            realName:'',
            style:0,
            userId:0,
            firstLogin:1
        }
    },
    mutations:{
        SET_TOKEN(state,token){
            state.token=token
        },
        ADD_PERMS(state,privilege){
            if(state.permitted===0){
            state.permitted=privilege
            if(state.permitted===1){
                state.permittedroutes=addUserRoute()
            }else if(state.permitted===2){
                state.permittedroutes=addRootRoute()
            }
            console.log(router)
        }
        },
        SET_USER(state,user){
            state.user.firstLogin=user.firstLogin
            state.user.username=user.username
            state.user.realName=user.realName
            state.user.userId=user.userId
            state.user.style=user.style
        },
        REMOVE_TOKEN(state){
            state.token=''
        },
        REMOVE_PERMS(state){
            state.permitted=0
            resetRouter()
        },
        UPDATE_USER_THEME(state,style){
            state.user.style=style
        }
    },
    actions:{
        LoginByUserName({commit},data){
            return new Promise((resolve,reject)=>{
                Login(data).then(res=>{
                    const token=res.data.data.token
                    commit('SET_TOKEN',token)
                    SetCookie(token)
                    resolve()
                }).catch(err=>{
                    reject(err)
                })
            })
        },
        GetUserInfoAction({commit},token){
            return new Promise((resolve,reject)=>{
                GetUserInfo(token).then(
                    res=>{
                        const user=res.data.data
                        commit('SET_USER',user)
                        commit('SET_TOKEN',token)
                        commit('ADD_PERMS',user.privilege)
                        resolve()
                    }).catch(
                        err=>{
                            reject(err)
                        }
                    )
            })
        },
        UserLogout({commit}){
            RemoveCookie()
            commit('REMOVE_PERMS')
            commit('REMOVE_TOKEN')
        },
        ChangePasswordByOldpassword({commit},data){
            return new Promise((resolve,reject)=>{
                changePasswordByOldpassword(data).then(()=>{
                    commit("REMOVE_TOKEN")
                    resolve()
                }).catch(err=>{
                    reject(err)
                })
            })
        },
        ChangePasswordByToken({commit},data){
            return new Promise((resolve,reject)=>{
                changePasswordByToken(data).then(()=>{
                    commit("REMOVE_TOKEN")
                    resolve()
                }).catch(err=>{
                    reject(err)
                })
            })
        },
        UpdateUserTheme({commit},style){
            commit("UPDATE_USER_THEME",style)
        }
    }
}