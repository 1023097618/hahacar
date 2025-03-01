import store from "@/store";
import axios from "axios";
import { Message } from "element-ui";
const baseurl = process.env.VUE_APP_baseurl
const tokenName = process.env.VUE_APP_tokenName
const service = axios.create(
    {
        baseURL: baseurl
    }
)
service.interceptors.request.use(
    config => {
        if (store.getters.token) {
            config.headers[tokenName] = store.getters.token
        }
        return config
    }
)

service.interceptors.response.use(
    config => {
        const data = config.data
        if (data.code && data.code !== "200") {
            //TODO 根据报错代码对错误进行提示
            return Promise.reject(data)
        }
        if (!data.code) {
            Message.error('后台服务器返回了意料外的结果')
            return Promise.reject('err')
        }
        return config
    }
)
export default service
