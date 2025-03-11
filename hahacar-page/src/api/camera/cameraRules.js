import request from '@/utils/request'

export function getCameraRules(params){
    return request({
        url:'/camera/getCameraRules',
        params,
        method:'get'
    })
}

export function updateCameraRules(data){
    return request({
        url:'camera/updateCameraRule',
        data,
        method:'post'
    })
}