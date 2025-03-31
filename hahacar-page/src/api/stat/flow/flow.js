import request from '@/utils/request'

export function searchFlowNum(params){
    return request({
        url:'/stat/flow/searchFlowNum',
        params,
        method:'get'
    })
}

export function getFlowMat(params){
    return request({
        url:'/stat/flow/getFlowMat',
        params,
        method:'get'
    })
}