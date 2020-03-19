<!--HTML代码-->
<template>
  <el-container>
    <el-main v-loading="loading" element-loading-text="查找中">
      <el-row>
        <el-col :span="18"><el-input v-model="post" @keyup.enter.native="search_data()"></el-input></el-col>
        <el-col :span="6"><el-button type="primary"  @click="search_data()">find</el-button></el-col>
      </el-row>
      <br/>
      <el-image v-if="!showGameInfo"
        src="https://s2.ax1x.com/2019/12/19/QqyRy9.jpg"
        fit="fill"></el-image>
      <el-card v-if="showGameInfo" class="box-card">
        <el-table
          :data="information.slice((current_page-1)*15,current_page*15)"
          style="width: 100%"
          @expand-change="exChange">
          <el-table-column type="expand">
            <template slot-scope="information">
              <el-container>
                <el-aside>
                  <el-col :span="1"><el-tag v-for="i in information.row.tags" :key="i">{{i}}</el-tag></el-col>
                </el-aside>
                <el-main>
                  <div :id="'gameChart'+information.row.name" :index="'gameChart'+information.row.name" :style="{width: '300px', height: '200px'}"></div>
                </el-main>
              </el-container>
            </template>
          </el-table-column>
          <el-table-column label="pic" width="180">
          <template slot-scope="information">
            <img :src="information.row.pic" width="100" height="50" class="head_pic"/>
          </template>
          </el-table-column>
          <el-table-column
            prop="name"
            label="名称"
            width="180">
          </el-table-column>
          <el-table-column
            prop="oprice"
            label="原始价格">
          </el-table-column>
          <el-table-column
            prop="cprice"
            label="目前价格">
          </el-table-column>
          <el-table-column
            prop="lprice"
            label="历史最低价格">
          </el-table-column>
        </el-table>
        <el-pagination
          background
          @current-change="handleCurrentChange"
          :current-page="current_page"
          :page-size="page_size"
          layout="prev, pager, next"
          :total="information.length" v-if="information.length > 15">
        </el-pagination>
      </el-card>
    </el-main>
  </el-container>
</template>
<script>
export default {
  name: 'steamGame',
  data () {
    return {
      error: null,
      post: null,
      loading: false,
      showGameInfo: false,
      information: null,
      search_way: 'steamid',
      current_page: 1,
      page_size: 15
    }
  },
  methods: {
    exChange (row, rowlist) {
      // eslint-disable-next-line eqeqeq
      if (row.expanding === true) {
        row.expanding = false
      } else if (row.expanding === false) {
        row.expanding = true
      } else {
        console.log('not find expand data')
        row.expanding = true
        this.$nextTick(() => { this.drawLine(row) })
      }
    },
    drawLine (item) {
      // 基于准备好的dom，初始化echarts实例
      // console.log(itemName)
      // console.log(this.$refs['gameChart' + itemName])
      let myChart = this.$echarts.init(document.getElementById('gameChart' + item.name))
      // 绘制图表
      myChart.setOption({
        title: { text: '价格浮动表' },
        tooltip: {},
        xAxis: {
          data: ['衬衫', '羊毛衫', '雪纺衫', '裤子', '高跟鞋', '袜子']
        },
        yAxis: {},
        series: [{
          name: '销量',
          type: 'bar',
          data: [5, 20, 36, 10, 10, 20]
        }]
      })
    },
    handleCurrentChange (val) {
      this.current_page = val
    },
    search_data () {
      if (this.post == null) {
        this.$message('please enter something')
        return
      }
      this.loading = true
      if (!this.isNumber(this.post)) {
        this.search_way = 'name'
      } else {
        this.search_way = 'steamid'
      }
      var params = new URLSearchParams()
      params.append(this.search_way, this.post)
      params.append('part', this.$route.params.part)
      this.$axios({
        method: 'post',
        url: '/api/block.php',
        data: params,
        timeout: 3000
      }).then(res => {
        this.information = res.data
        this.loading = false
        if (this.information.length === 0) {
          this.$message({message: 'can\'t find', type: 'error'})
          this.showGameInfo = false
          return
        }
        if (this.information[0].name === null) {
          this.$message({message: 'can\'t find', type: 'error'})
          this.showGameInfo = false
          return
        }
        this.$message({message: 'success', type: 'success'})
        this.showGameInfo = true
      }).catch((error) => {
        this.loading = false
        console.log(error)
        this.showGameInfo = false
        this.$message({message: 'we has some problem', type: 'error'})
      })
    },
    isNumber (value) {
      var patrn = /^(-)?\d+(\.\d+)?$/
      if (patrn.exec(value) === null || value === '') {
        return false
      } else {
        return true
      }
    }
  }
}
</script>
