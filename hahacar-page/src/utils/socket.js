import {io} from 'socket.io-client'
import store from '@/store'
const socket= io(process.env.VUE_APP_socket_base,{
    path:process.env.VUE_APP_socket_path
})
socket.on("updateProgress",(data)=>{
    store.dispatch("UpdateTasks",data)
})
socket.on("doneProgress",data=>{
    store.dispatch("UpdateTasks",data)
})
socket.on("connect",()=>{
    store.dispatch("UpdateSocketId",socket.id)
})
export default socket