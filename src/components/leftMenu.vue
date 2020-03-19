
<template>
  <el-row class="tac">
    <el-col :span="20">
      <h5>分类</h5>
      <el-menu
        default-active="2"
        background-color="#fff"
        text-color="#C0C0C0"
        active-text-color="#000"
        class="el-menu-vertical-demo">
        <el-menu-item v-for="item in left" :key="item" :index="item" @click="changeto(item)">
          <span slot="title">{{item}}</span>
        </el-menu-item>
      </el-menu>
    </el-col>
  </el-row>
</template>

<script>
export default {
  data () {
    return {
      left: ['Indie', 'RPG', 'Simulation', 'Racing', 'Sports', 'Strategy', 'Massively Multiplayer', 'Action', 'Adventure', 'Casual']
    }
  },
  methods: {
    changeto (item) {
      if (this.$route.params.part === item) {
        return
      }
      this.$router.push({path: item})
    }
  }
}
</script>
