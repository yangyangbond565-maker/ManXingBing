import axios from 'axios'

const http = axios.create({ baseURL: '/api', timeout: 30000 })
http.interceptors.response.use(
  (response) => {
    const body = response.data
    if (body && typeof body.code !== 'undefined') {
      if (body.code !== 0) return Promise.reject(new Error(body.message || '接口返回错误'))
      return body.data
    }
    return body
  },
  (error) => {
    const message = error.response?.data?.message || error.message || '网络请求失败'
    return Promise.reject(new Error(message))
  }
)

export const getOverview = () => http.get('/dashboard/overview')
export const getProfile = () => http.get('/patient-profile')
export const getDisease = () => http.get('/disease-distribution')
export const getRisk = (factor) => http.get('/risk-factors', { params: { factor } })
export const getVisits = (type) => http.get('/visits', { params: { type } })
export const getMedications = (type) => http.get('/medications', { params: { type } })
export const getTrend = (grain = 'year') => http.get('/trend', { params: { grain } })
export const getHealthOverview = () => http.get('/health-score/overview')
export const getHealthPatients = (params) => http.get('/health-score/patients', { params })
export const getPatients = (params) => http.get('/patients', { params })
export const getPatientDetail = (id) => http.get('/patients/' + id)
export const getDataQuality = () => http.get('/data-quality')
export const getModules = () => http.get('/modules')
export const getApiHealth = () => http.get('/health')
export default http
