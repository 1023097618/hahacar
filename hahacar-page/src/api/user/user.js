import request from '@/utils/request'

export function styleChange(data){
    return request({
        url:'/user/styleChange',
        data,
        method:'post'
    })
}

export function getUsers(params){
    return request({
        url:'/user/getUsers',
        params,
        method:'get'
    })
}

export function updateUser(data){
    return request({
        url:'/user/updateUsers',
        data,
        method:'post'
    })
}

export function deleteUser(data){
    return request({
        url:'/user/deleteUsers',
        data,
        method:'delete'
    })
}

export function addUser(data){
    return request({
        url:'/user/addUser',
        data,
        method:'post'
    })
}

export function getUserCameraPrivilege(params){
    return request({
        url:'/user/getUserCameraPrivilege',
        params,
        method:'get'
    })
}

export function updateUserCameraPrivilege(data){
    return request({
        url:'/user/updateUserCameraPrivilege',
        data,
        method:'post'
    })
}