import request from '@/utils/request'

export function searchHoldNum(params){
    return request({
        url:'/stat/hold/searchHoldNum',
        params,
        method:'get'
    })
}