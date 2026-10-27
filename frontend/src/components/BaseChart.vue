<template>
  <div v-loading="loading" class="chart-wrap" :style="{ height }">
    <div ref="chartRef" class="chart"></div>
    <el-empty v-if="!loading && empty" description="暂无数据" :image-size="72" />
  </div>
</template>
<script setup>
import { onBeforeUnmount, onMounted, ref, watch, nextTick } from 'vue'
import * as echarts from 'echarts'
const props = defineProps({ option: { type: Object, default: () => ({}) }, height: { type: String, default: '320px' }, loading: Boolean, empty: Boolean })
const chartRef = ref(null)
let chart = null
let observer = null
function render() {
  if (!chartRef.value) return
  if (!chart) chart = echarts.init(chartRef.value)
  chart.setOption(props.option || {}, true)
}
onMounted(() => { nextTick(render); observer = new ResizeObserver(() => chart && chart.resize()); observer.observe(chartRef.value) })
watch(() => props.option, () => nextTick(render), { deep: true })
onBeforeUnmount(() => { observer && observer.disconnect(); chart && chart.dispose() })
</script>
<style scoped>
.chart-wrap { position: relative; width: 100%; }
.chart { width: 100%; height: 100%; }
.chart-wrap :deep(.el-empty) { position: absolute; inset: 0; background: #fff; }
</style>
