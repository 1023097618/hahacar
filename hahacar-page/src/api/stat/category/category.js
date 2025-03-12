import request from '@/utils/request'

export function searchCategoryNum(params){
    return request({
        url:'/stat/category/searchCategoryNum',
        params,
        method:'get'
    })
}