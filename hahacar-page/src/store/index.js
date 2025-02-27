import Vue from 'vue'
import Vuex from 'vuex'
import url from './modules/url'
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
    url
  }
})
