import request from '@/utils/request.js'

export function getAlerts(params){
    return request({
        url:'/alert/getAlerts',
        method:'get',
        params
    })
}

export function processAlert(data){
    return request({
        url:'/alert/processAlert',
        method:'post',
        data
    })
}