import Vue from 'vue'
import Vuex from 'vuex'
import user from './modules/user'
import socket from './modules/socket'
import getters from './getters'
Vue.use(Vuex)


export default new Vuex.Store({
  state: {
  },
  getters,
  mutations: {
  },
  actions: {
  },
  modules: {
    user,
    socket
  }
})
