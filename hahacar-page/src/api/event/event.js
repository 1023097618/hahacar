import request from '@/utils/request'

export function getEvents(){
    return request({
        url:'/event/getEvents',
        method:'get'
    })
}