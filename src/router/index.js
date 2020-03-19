import main from '@/components/main'
import leftMenu from '@/components/leftMenu'
const Vue = require('vue')
const Router = require('vue-router')
const axios = require('axios')

axios.defaults.headers.post['Content-Type'] = 'application/x-www-form-urlencoded'
Vue.prototype.$axios = axios
export default new Router({
  routes: [{
    path: '/',
    redirect: '/Action',
    name: '主页'
  },
  {
    path: '/:part/',
    name: 'game',
    components: {
      default: main,
      left: leftMenu
    }
  }
  ]
})
