import request from '@/utils/request'

export function Login(data){
    return request({
        url:'/auth/login',
        data,
        method:'post'
    })
}

export function GetUserInfo(token){
    return request({
        url:'/auth/info',
        params:{
            token:token
        },
        method:'get'
    })
}

export function changePasswordByOldpassword(data){
    return request({
        url:'/auth/changePasswordByOldpassword',
        data,
        method:'post'
    })
}

export function changePasswordByToken(data){
    return request({
        url:'/auth/changePasswordByToken',
        data,
        method:'post'
    })
}