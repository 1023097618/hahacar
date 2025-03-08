import request from '@/utils/request'
const baseurl = process.env.VUE_APP_baseurl

export function uploadVideo(data){
    return request({
        url:'/storage/videoUpload',
        headers:{ "Content-Type": "multipart/form-data" },
        data:data,
        method:'post'
    })
}

export function uploadPicture(data){
    return request({
        url:'/storage/pictureUpload',
        headers:{ "Content-Type": "multipart/form-data" },
        data:data,
        method:'post'
    })
}

export const getCameraLiveStream=baseurl+"/storage/getCameraLiveStream"