<template>
  <div class="rules-container">
    <h2>摄像头规则配置 - 摄像头ID：{{ cameraId }}</h2>
    <!-- 添加规则按钮 -->
    <el-button type="primary" @click="addRule" style="margin-bottom: 20px;">添加规则</el-button>

    <!-- 规则列表 -->
    <div v-for="(rule, index) in rules" :key="index" class="rule-card">
      <el-card shadow="hover" style="margin-bottom: 20px;">
        <div slot="header" class="clearfix">
          <span>规则 {{ index + 1 }}</span>
          <el-button type="text" style="float: right;" @click="removeRule(index)">删除</el-button>
        </div>
        <el-form :model="rule" label-width="120px">
          <el-form-item label="规则类型">
            <el-select v-model="rule.ruleValue" placeholder="请选择规则类型" style="width: 200px;"
              @change="handleRuleTypeChange(rule)">
              <el-option label="车辆类别预警" value="1"></el-option>
              <el-option label="车辆拥堵预警" value="2"></el-option>
              <el-option label="车流量预警" value="3"></el-option>
              <el-option label="车辆预约检测" value="4"></el-option>
              <el-option label="异常事故预警" value="5"></el-option>
            </el-select>
          </el-form-item>

          <!-- 当规则类型为1：车辆类别预警时 -->
          <div v-if="rule.ruleValue === '1'">
            <el-form-item label="选择标签">
              <el-select v-model="rule.labelId" multiple placeholder="请选择标签" style="width: 300px;">
                <el-option v-for="item in labels" :key="item.labelId" :label="item.labelName" :value="item.labelId">
                </el-option>
              </el-select>
            </el-form-item>
          </div>

          <!-- 当规则类型为2：车辆拥堵预警时 -->
          <div v-if="rule.ruleValue === '2'">
            <el-form-item label="最大交通当量">
              <el-input v-model="rule.VehicleHold.maxVehicleHoldNum" placeholder="例如：1.5"
                style="width:200px;"></el-input>
            </el-form-item>
            <el-form-item label="最大持续时长">
              <el-input-number v-model="rule.VehicleHold.maxContinuousTimePeriod" :min="0"></el-input-number>
            </el-form-item>
            <el-form-item label="最小交通当量">
              <el-input v-model="rule.VehicleHold.minVehicleHoldNum" placeholder="例如：1.0"
                style="width:200px;"></el-input>
            </el-form-item>
            <el-form-item label="最小持续时长">
              <el-input-number v-model="rule.VehicleHold.minContinuousTimePeriod" :min="0"></el-input-number>
            </el-form-item>
            <el-form-item label="交通当量设置">
              <div v-for="(item, i) in rule.VehicleHold.LabelsEqual" :key="i" class="labels-equal-item">
                <el-select v-model="item.labelId" placeholder="选择标签" style="width:150px;">
                  <el-option v-for="label in labels" :key="label.labelId" :label="label.labelName"
                    :value="label.labelId">
                  </el-option>
                </el-select>
                <el-input v-model="item.labelHoldNum" placeholder="当量"
                  style="width:100px; margin-left:10px;"></el-input>
                <el-button type="text" @click="removeLabelsEqual(rule.VehicleHold.LabelsEqual, i)">删除</el-button>
              </div>
              <el-button type="primary" @click="addLabelsEqual(rule, 'VehicleHold')">添加当量设置</el-button>
            </el-form-item>
          </div>

          <!-- 当规则类型为3：车流量预警时 -->
          <div v-if="rule.ruleValue === '3'">
            <el-form-item label="最大交通当量">
              <el-input v-model="rule.VehicleFlow.maxVehicleFlowNum" placeholder="例如：1.5"
                style="width:200px;"></el-input>
            </el-form-item>
            <el-form-item label="最大持续时长">
              <el-input-number v-model="rule.VehicleFlow.maxContinuousTimePeriod" :min="0"></el-input-number>
            </el-form-item>
            <el-form-item label="最小交通当量">
              <el-input v-model="rule.VehicleFlow.minVehicleFlowNum" placeholder="例如：1.0"
                style="width:200px;"></el-input>
            </el-form-item>
            <el-form-item label="最小持续时长">
              <el-input-number v-model="rule.VehicleFlow.minContinuousTimePeriod" :min="0"></el-input-number>
            </el-form-item>
            <el-form-item label="交通当量设置">
              <div v-for="(item, i) in rule.VehicleFlow.LabelsEqual" :key="i" class="labels-equal-item">
                <el-select v-model="item.labelId" placeholder="选择标签" style="width:150px;">
                  <el-option v-for="label in labels" :key="label.labelId" :label="label.labelName"
                    :value="label.labelId">
                  </el-option>
                </el-select>
                <el-input v-model="item.labelEqualNum" placeholder="当量"
                  style="width:100px; margin-left:10px;"></el-input>
                <el-button type="text" @click="removeLabelsEqual(rule.VehicleFlow.LabelsEqual, i)">删除</el-button>
              </div>
              <el-button type="primary" @click="addLabelsEqual(rule, 'VehicleFlow')">添加当量设置</el-button>
            </el-form-item>
            <el-form-item label="摄像头起始线">
              <el-select v-model="rule.VehicleFlow.cameraStartLine.cameraLineId" placeholder="选择起始检测线"
                style="width:200px;">
                <el-option v-for="line in cameraLines" :key="line.cameraLineId" :label="line.cameraLineName"
                  :value="line.cameraLineId">
                </el-option>
              </el-select>
              <el-checkbox v-model="rule.VehicleFlow.cameraStartLine.isAll" style="margin-left:10px;">全部</el-checkbox>
            </el-form-item>
            <el-form-item label="摄像头终止线">
              <el-select v-model="rule.VehicleFlow.cameraEndLine.cameraLineId" placeholder="选择终止检测线"
                style="width:200px;">
                <el-option v-for="line in cameraLines" :key="line.cameraLineId" :label="line.cameraLineName"
                  :value="line.cameraLineId">
                </el-option>
              </el-select>
              <el-checkbox v-model="rule.VehicleFlow.cameraEndLine.isAll" style="margin-left:10px;">全部</el-checkbox>
            </el-form-item>
          </div>

          <!-- 当规则类型为4：车辆预约检测时 -->
          <div v-if="rule.ruleValue === '4'">
            <el-form-item label="预约车辆检测">
              <el-checkbox v-model="rule.VehicleReserve">开启预约车辆检测</el-checkbox>
            </el-form-item>
          </div>

          <!-- 当规则类型为5：异常事故预警时 -->
          <div v-if="rule.ruleValue === '5'">
            <el-form-item label="开启事故预警">
              <el-checkbox v-model="rule.eventDetect">开启事故预警</el-checkbox>
            </el-form-item>
          </div>
        </el-form>
      </el-card>
    </div>

    <!-- 保存与返回按钮 -->
    <el-button type="primary" @click="saveRules">保存规则</el-button>
    <el-button style="margin-left: 10px;" @click="goBack">返回</el-button>
  </div>
</template>

<script>
  import { getCameraRules, updateCameraRules } from '@/api/camera/cameraRules.js'
  import { getLabels } from '@/api/label/label.js'
  import { getCameraLines } from '@/api/camera/cameraLines'
  export default {
    name: 'cameraRulesView',
    data() {
      return {
        cameraId: '',     // 从路由query中获取
        rules: [],        // 规则列表
        labels: [],       // 可选标签
        cameraLines: []   // 摄像头检测线列表
      }
    },
    created() {
      // 获取路由参数中的cameraId
      this.cameraId = this.$route.query.cameraId || ''
      this.fetchRules()
      this.fetchLabels()
      this.fetchCameraLines()
    },
    methods: {
      // 获取当前摄像头的规则配置
      fetchRules() {
        if (!this.cameraId) return
        getCameraRules({ cameraId: this.cameraId }).then(response => {
          const data = response.data.data
          this.rules = (data.cameraRules && data.cameraRules.length > 0) ? data.cameraRules : []
        }).catch(() => {
          this.$notify.error({
            title: '错误',
            message: '获取规则失败'
          })
        })
      },
      // 获取标签列表
      fetchLabels() {
        getLabels().then(response => {
          const data = response.data.data
          this.labels = data.labels || []
        }).catch(() => {
          this.$notify.error({
            title: '错误',
            message: '获取标签失败'
          })
        })
      },
      // 获取摄像头检测线列表
      fetchCameraLines() {
        getCameraLines({ cameraId: this.cameraId }).then(response => {
          const data = response.data.data
          this.cameraLines = data.cameraLines || []
        }).catch(() => {
          this.$notify.error({
            title: '错误',
            message: '获取检测线失败'
          })
        })
      },
      // 添加新规则，默认规则类型为“车辆类别预警”
      addRule() {
        this.rules.push({
          ruleValue: '1',
          labelId: []
        })
      },
      // 删除指定规则
      removeRule(index) {
        this.rules.splice(index, 1)
      },
      // 根据规则类型添加当量设置项
      addLabelsEqual(rule, type) {
        if (type === 'VehicleHold') {
          if (!rule.VehicleHold) {
            // 初始化拥堵预警规则的对象
            this.$set(rule, 'VehicleHold', {
              maxVehicleHoldNum: '',
              maxContinuousTimePeriod: 0,
              minVehicleHoldNum: '',
              minContinuousTimePeriod: 0,
              LabelsEqual: []
            })
          }
          rule.VehicleHold.LabelsEqual.push({ labelId: '', labelHoldNum: '' })
        } else if (type === 'VehicleFlow') {
          if (!rule.VehicleFlow) {
            // 初始化车流量预警规则的对象
            this.$set(rule, 'VehicleFlow', {
              maxVehicleFlowNum: '',
              maxContinuousTimePeriod: 0,
              minVehicleFlowNum: '',
              minContinuousTimePeriod: 0,
              LabelsEqual: [],
              cameraStartLine: { cameraLineId: '', isAll: false },
              cameraEndLine: { cameraLineId: '', isAll: false }
            })
          }
          rule.VehicleFlow.LabelsEqual.push({ labelId: '', labelEqualNum: '' })
        }
      },
      // 删除当量设置中的某一项
      removeLabelsEqual(labelsEqualArray, index) {
        labelsEqualArray.splice(index, 1)
      },
      // 保存当前所有规则配置
      saveRules() {
        const payload = {
          cameraId: this.cameraId,
          cameraRules: this.rules
        }
        updateCameraRules(payload).then(() => {
          this.$notify.success({
            title: '成功',
            message: '规则更新成功'
          })
        }).catch(() => {
          this.$notify.error({
            title: '失败',
            message: '规则更新失败'
          })
        })
      },
      handleRuleTypeChange(rule) {
        // 如果选择车辆类别预警，删除VehicleHold和VehicleFlow
        if (rule.ruleValue === '1') {
          if (rule.VehicleHold) {
            delete rule.VehicleHold;
          }
          if (rule.VehicleFlow) {
            delete rule.VehicleFlow;
          }
          if (rule.VehicleReserve !== undefined) {
            delete rule.VehicleReserve;
          }
          if (rule.eventDetect !== undefined) {
            delete rule.eventDetect;
          }
        }
        // 如果选择车辆拥堵预警，只初始化VehicleHold，并删除VehicleFlow
        else if (rule.ruleValue === '2') {
          this.$set(rule, 'VehicleHold', {
            maxVehicleHoldNum: '',
            maxContinuousTimePeriod: 0,
            minVehicleHoldNum: '',
            minContinuousTimePeriod: 0,
            LabelsEqual: []
          });
          if (rule.VehicleFlow) {
            delete rule.VehicleFlow;
          }
          if (rule.VehicleReserve !== undefined) {
            delete rule.VehicleReserve;
          }
          if (rule.eventDetect !== undefined) {
            delete rule.eventDetect;
          }
        }
        // 如果选择车流量预警，只初始化VehicleFlow，并删除VehicleHold
        else if (rule.ruleValue === '3') {
          this.$set(rule, 'VehicleFlow', {
            maxVehicleFlowNum: '',
            maxContinuousTimePeriod: 0,
            minVehicleFlowNum: '',
            minContinuousTimePeriod: 0,
            LabelsEqual: [],
            startLine: '',
            cameraStartLine: { cameraLineId: '', isAll: false },
            cameraEndLine: { cameraLineId: '', isAll: false }
          });
          if (rule.VehicleHold) {
            delete rule.VehicleHold;
          }
          if (rule.VehicleReserve !== undefined) {
            delete rule.VehicleReserve;
          }
          if (rule.eventDetect !== undefined) {
            delete rule.eventDetect;
          }
        }
        // 新增：如果选择车辆预约检测，初始化VehicleReserve，并删除其他多余属性
        else if (rule.ruleValue === '4') {
          this.$set(rule, 'VehicleReserve', false);
          if (rule.VehicleHold) { delete rule.VehicleHold; }
          if (rule.VehicleFlow) { delete rule.VehicleFlow; }
          if (rule.eventDetect !== undefined) { delete rule.eventDetect; }
        }
        // 新增：如果选择异常事故预警，初始化eventId，并删除其他多余属性
        else if (rule.ruleValue === '5') {
          this.$set(rule, 'eventDetect', false);
          if (rule.VehicleHold) { delete rule.VehicleHold; }
          if (rule.VehicleFlow) { delete rule.VehicleFlow; }
          if (rule.VehicleReserve !== undefined) { delete rule.VehicleReserve; }
          if (rule.labelId !== undefined) { delete rule.labelId; }
        }
      },
      // 返回上一级
      goBack() {
        this.$router.back()
      }
    }
  }
</script>

<style scoped>
  .rules-container {
    padding: 20px;
  }

  .rule-card {
    margin-bottom: 20px;
  }

  .labels-equal-item {
    display: flex;
    align-items: center;
    margin-bottom: 10px;
  }
</style>