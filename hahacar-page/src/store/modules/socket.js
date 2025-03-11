//专门处理websocket有关的数据存储，使用户能第一时间获取到相关的数据。
//网上好像这方面的资料挺少的，我不确定这个文件名是不是叫socket.js，或许有更规范的命名方式？
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
        sid:-1
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
        }
    },
    actions:{
        UpdateTasks({commit},data){
            commit("UPDATE_TASKS",data)
        },
        UpdateSocketId({commit},sid){
            commit("UPDATE_SOCKET_ID",sid)
        }
    }
}