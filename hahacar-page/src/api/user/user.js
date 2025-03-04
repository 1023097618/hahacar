import request from '@/utils/request'

export function styleChange(data){
    return request({
        url:'/user/styleChange',
        data,
        method:'post'
    })
}