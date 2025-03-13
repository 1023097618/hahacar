import request from '@/utils/request'

import { GetCookie } from '@/utils/auth'

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

// export function getCameraLiveURL(cameraId,liveStreamType){
//     const baseurl = process.env.VUE_APP_baseurl
//     const token=GetCookie(cameraId)
//     return `${baseurl}/storage/getCameraLiveStream?token=${token}&cameraId=${cameraId}&liveStreamType=${liveStreamType}`
// }

export function getCameraLiveURL(){
    const c= parseInt(new Date().getTime()/1000);
    return `http://220.254.72.200/cgi-bin/camera?resolution=640&amp;quality=1&amp;Language=0&amp;${c}`
}


export function getImageURL(fileName){
    const token=GetCookie()
    return `${process.env.VUE_APP_image_baseurl}/${fileName}?token=${token}`
}