import request from '@/utils/request'

export function getLabels(){
    return request({
        url:'/label/getLabels',
        method:'get'
    })
}