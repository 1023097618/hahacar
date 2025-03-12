import {io} from 'socket.io-client'
import store from '@/store'
import { GetCookie } from '@/utils/auth'
const tokenName=process.env.VUE_APP_tokenName
const socket= io(process.env.VUE_APP_socket_base,{
    // path:process.env.VUE_APP_socket_path,
    auth:{
        [tokenName]:GetCookie()
    },
    transports: ["websocket"]
})
socket.on("updateProgress",(data)=>{
    store.dispatch("UpdateTasks",data)
})
socket.on("doneProgress",data=>{
    store.dispatch("UpdateTasks",data)
})
socket.on("connect", () => {
    store.dispatch("UpdateSocketId", socket.id)
})

socket.on('updateHappeningAlert', (data) => {
    store.dispatch("AddAlert", data)
})

socket.on('cameraSituation', (data) => {
    store.dispatch("UpdateCameraSituation", data)
})
export default socket