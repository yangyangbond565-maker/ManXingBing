import { createRouter, createWebHashHistory } from 'vue-router'
import MainLayout from '../layouts/MainLayout.vue'

const routes = [
  { path: '/', redirect: '/home' },
  { path: '/home', component: MainLayout, children: [{ path: '', name: 'home', component: () => import('../views/Home.vue'), meta: { title: '系统首页' } }] },
  { path: '/profile', component: MainLayout, children: [{ path: '', component: () => import('../views/PatientProfile.vue'), meta: { title: '患者画像' } }] },
  { path: '/disease', component: MainLayout, children: [{ path: '', component: () => import('../views/DiseaseDistribution.vue'), meta: { title: '疾病分布分析' } }] },
  { path: '/risk', component: MainLayout, children: [{ path: '', component: () => import('../views/RiskFactors.vue'), meta: { title: '风险因素关联' } }] },
  { path: '/visits', component: MainLayout, children: [{ path: '', component: () => import('../views/Visits.vue'), meta: { title: '就诊行为分析' } }] },
  { path: '/medications', component: MainLayout, children: [{ path: '', component: () => import('../views/Medications.vue'), meta: { title: '用药分析' } }] },
  { path: '/trend', component: MainLayout, children: [{ path: '', component: () => import('../views/Trend.vue'), meta: { title: '疾病趋势预测' } }] },
  { path: '/health', component: MainLayout, children: [{ path: '', component: () => import('../views/HealthScore.vue'), meta: { title: '健康评分' } }] },
  { path: '/patients', component: MainLayout, children: [{ path: '', component: () => import('../views/Patients.vue'), meta: { title: '患者查询' } }] },
  { path: '/data-quality', component: MainLayout, children: [{ path: '', component: () => import('../views/DataQuality.vue'), meta: { title: '数据质量' } }] },
  { path: '/screen', name: 'screen', component: () => import('../views/BigScreen.vue') },
  { path: '/:pathMatch(.*)*', component: MainLayout, children: [{ path: '', component: () => import('../views/NotFound.vue') }] }
]
export default createRouter({ history: createWebHashHistory(), routes, scrollBehavior: () => ({ top: 0 }) })
