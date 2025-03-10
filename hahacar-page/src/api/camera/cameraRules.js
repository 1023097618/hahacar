import request from '@/utils/request'

export default function getCameraRules(params){
    return request({
        url:'/camera/getCameraRules',
        params,
        method:'get'
    })
}

export default function updateCameraRules(data){
    return request({
        url:'camera/updateCameraRules',
        data,
        method:'post'
    })
}