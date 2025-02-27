import request from '@/utils/request'

export function upload(data){
    return request({
        url:'/storage/vedioupload',
        headers:{ "Content-Type": "multipart/form-data" },
        data:data,
        method:'post'
    })
}