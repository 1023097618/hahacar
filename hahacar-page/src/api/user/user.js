import request from '@/utils/request'

export function styleChange(data){
    return request({
        url:'/auth/styleChange',
        data,
        method:'post'
    })
}