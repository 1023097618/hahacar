//专门处理websocket有关的数据存储，使用户能第一时间获取到相关的数据。
//网上好像这方面的资料挺少的，我不确定这个文件名是不是叫socket.js，或许有更规范的命名方式？
import Vue from 'vue'
export default{
    state:{
        tasks:[
            // {
            //     taskId:"34",
            //     isComplete:false,
            //     progressValue:20,
            //     downloadURL:"http://",
            //     watchURL:"http://"
            // }
        ],
        sid:-1,
        alertMessages: [],
        cameraSituations: {}
    },
    mutations:{
        UPDATE_TASKS(state,data){
            if(data.type==="picture"){
                state.tasks.push({
                    downloadURL:data.downloadURL,
                    watchURL:data.watchURL,
                    type:data.type,
                    isComplete:true,
                    fileName:data.fileName
                }
                )
                return;
            }
            const taskId=data.taskId
            const taskIndex=state.tasks.findIndex(task=>task.taskId===taskId)
            if(taskIndex===-1){
                state.tasks.push(
                    {
                        taskId,
                        isComplete: data.progressValue !== null ?data.progressValue === 100:true,
                        progressValue: data.progressValue !== null?data.progressValue:100,
                        downloadURL: data.downloadURL?data.downloadURL:undefined,
                        watchURL:data.watchURL?data.watchURL:undefined,
                        type:'video',
                        fileName:data.fileName
                    }
                )
            }else{
                if(data.downloadURL){
                    state.tasks[taskIndex].isComplete=true
                    state.tasks[taskIndex].progressValue=100
                    state.tasks[taskIndex].downloadURL=data.downloadURL
                    state.tasks[taskIndex].watchURL=data.watchURL
                }else{
                    state.tasks[taskIndex].isComplete=data.progressValue===100
                    state.tasks[taskIndex].progressValue=data.progressValue
                }
            }
        },
        UPDATE_SOCKET_ID(state,sid){
            state.sid=sid
        },
        UPDATE_CAMERA_SITUATION(state, data) {
            // 如果 data 是数组，则遍历每一项处理；否则直接处理单个对象
            if (Array.isArray(data)) {
                data.forEach(item => {
                    if (item && item.cameraId) {
                        Vue.set(state.cameraSituations, item.cameraId, {
                            online: item.online,
                            alert: item.alert
                        })
                    }
                })
            } else {
                if (data && data.cameraId) {
                    Vue.set(state.cameraSituations, data.cameraId, {
                        online: data.online,
                        alert: data.alert
                    })
                }
            }
        },
        ADD_ALERT(state, alert) {
            // 如果 alert 是数组，则遍历每一项；否则直接添加
            if (Array.isArray(alert)) {
                alert.forEach(item => {
                    state.alertMessages.push(item)
                })
            } else {
                state.alertMessages.push(alert)
            }
        }
    },
    actions:{
        UpdateTasks({commit},data){
            commit("UPDATE_TASKS",data)
        },
        UpdateSocketId({commit},sid){
            commit("UPDATE_SOCKET_ID",sid)
        },
        AddAlert({commit},data){
            commit("ADD_ALERT",data)
        },
        UpdateCameraSituation({commit},data){
            commit("UPDATE_CAMERA_SITUATION",data)
        },
    }
}