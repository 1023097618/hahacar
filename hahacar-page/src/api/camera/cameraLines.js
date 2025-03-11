import request from '@/utils/request'

export function getCameraLines(params){
    return request({
        url:'/camera/getCameraLines',
        params,
        method:'get'
    })
}