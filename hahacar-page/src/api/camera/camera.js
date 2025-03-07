import request from '@/utils/request'

export function getCameraList(params){
    return request({
        url:'/camera/getCameras',
        params,
        method:'get'
    })
}

export function deleteCamera(data){
    return request({
        url:'/camera/deleteCamera',
        data,
        method:'delete'
    })
}

export function updateCamera(data){
    return request({
        url:'/camera/updateCamera',
        data,
        method:'post'
    })
}

export function addCamera(data){
    return request({
        url:'/camera/addCamera',
        data,
        method:'post'
    })
}