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
                <el-main :id="'gameChart'+information.row.name" :index="'gameChart'+information.row.name" :style="{height: '300px'}"></el-main>
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
      page_size: 15,
      timelist: [],
      valuelist: [],
      currentItem: null
    }
  },
  methods: {
    exChange (row, rowlist) {
      // eslint-disable-next-line eqeqeq
      if (row.expanding === true) {
        row.expanding = false
      } else if (row.expanding === false) {
        row.expanding = true
        this.search_price(row)
        this.currentItem = row
        this.valuelist = []
        this.timelist = []
      } else {
        console.log('not find expand data')
        row.expanding = true
        this.search_price(row)
        this.currentItem = row
        this.valuelist = []
        this.timelist = []
        // this.$nextTick(() => {
        //   this.search_price(row.steamid)
        //   this.drawLine(row)
        // })
      }
    },
    search_price (row) {
      var priceParam = new URLSearchParams()
      priceParam.append('flag', '1')
      priceParam.append('steamid', row.steamid)
      priceParam.append('part', this.$route.params.part)
      this.$axios({
        method: 'post',
        url: '/api/block.php',
        data: priceParam,
        timeout: 3000
      }).then(res => {
        // console.log(res)
        if (res.data.length === 0) {
          var date = new Date()
          this.valuelist = [parseFloat(row.oprice), parseFloat(row.cprice)]
          this.timelist = ['begin', this.getTime(date)]
          return
        }
        var data = res.data
        this.valuelist.push(parseFloat(this.currentItem.oprice))
        this.timelist.push('begin')
        for (var i = 0; i < data.length; i++) {
          // console.log(data[i])
          // console.log(data[i].price)
          this.valuelist.push(parseFloat(data[i].price))
          this.timelist.push(data[i].date.split(' ')[0].toString())
        }
        // console.log(this.valuelist)
        // console.log(this.timelist)
      }).catch((error) => {
        console.log(error)
      })
    },
    drawLine (item) {
      // 基于准备好的dom，初始化echarts实例
      // console.log(this.valuelist)
      // console.log(this.timelist)
      // console.log(itemName)
      // console.log(this.$refs['gameChart' + itemName])
      try {
        var target = document.getElementById('gameChart' + item.name)
        if (target == null) { return }
      } catch (e) {
        console.log(e)
        return
      }
      let myChart = this.$echarts.init(target)
      // 绘制图表
      myChart.setOption({
        title: { text: '价格浮动表' },
        tooltip: {},
        xAxis: {
          axisLabel: {
            interval: 0,
            rotate: 30
          },
          type: 'category',
          data: this.timelist
        },
        yAxis: {
          show: true,
          type: 'value',
          splitLine: {show: false}, // 去除网格线
          nameTextStyle: {
            color: '#abb8ce'
          },
          axisLabel: {
            color: '#abb8ce'
          },
          axisTick: { // y轴刻度线
            show: false
          },
          axisLine: { // y轴
            show: false
          }
        },
        series: [{
          name: '价格',
          type: 'line',
          smooth: true,
          data: this.valuelist
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
    },
    getTime (date) {
      let y = date.getFullYear()
      let MM = date.getMonth() + 1
      MM = MM < 10 ? ('0' + MM) : MM
      let d = date.getDate()
      d = d < 10 ? ('0' + d) : d
      return y + '-' + MM + '-' + d
    }
  },
  watch: {
    timelist () {
      this.drawLine(this.currentItem)
    }
  }
}
</script>
