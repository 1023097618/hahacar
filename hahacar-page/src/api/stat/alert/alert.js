import request from '@/utils/request'

export function searchAlertNum(params){
    return request({
        url:'/stat/alert/searchAlertNum',
        params,
        method:'get'
    })
}