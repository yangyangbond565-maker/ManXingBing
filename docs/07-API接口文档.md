# 07 API 接口文档

## 1. 基础信息

- Base URL：http://127.0.0.1:8080/api
- 前端代理：http://127.0.0.1:4173/api
- 编码：UTF-8
- 方法：全部 GET（只读查询）
- 认证：教学环境未启用登录；生产需增加认证与鉴权
- 统一响应：

~~~json
{"code":0,"message":"ok","data":{}}
~~~

- code=0 成功；400 参数错误；404 未找到；500 服务器异常。
- 分页响应 data 结构：records、total、page、size。

## 2. 接口列表

| 方法 | 路径 | 参数 | 说明 |
|---|---|---|---|
| GET | /health | - | 服务状态 |
| GET | /dashboard/overview | - | 大屏总览 |
| GET | /patient-profile | - | 患者画像 |
| GET | /disease-distribution | - | 疾病/严重度/共病 |
| GET | /risk-factors | factor 可选 | 风险因素 |
| GET | /visits | type 可选 | 就诊分析 |
| GET | /medications | type 可选 | 用药分析 |
| GET | /trend | grain=year/month | 趋势预测 |
| GET | /health-score/overview | - | 评分总览 |
| GET | /health-score/patients | page,size,level,keyword,gender,province,minAge,maxAge | 评分分页 |
| GET | /patients | page,size,keyword,gender,province,level,minAge,maxAge | 患者分页 |
| GET | /patients/{id} | 路径参数 | 患者完整档案 |
| GET | /data-quality | - | 数据质量 |
| GET | /modules | - | 八模块状态 |

## 3. 关键接口示例

### 3.1 总览

请求：GET /api/dashboard/overview

响应数据（节选）：

~~~json
{
  "totalPatients": 100000,
  "totalDiseaseRecords": 165087,
  "totalVisits": 550070,
  "totalMedications": 549587,
  "totalFollowups": 300390,
  "avgHealthScore": 72.8,
  "highRiskCount": 1718,
  "highRiskRate": 1.72,
  "totalCost": 6405901105.17,
  "avgCost": 11645.61,
  "dataStartYear": 2018,
  "dataEndYear": 2025
}
~~~

### 3.2 患者分页

请求：GET /api/patients?page=1&size=10&gender=女&level=良好

响应 data：

~~~json
{
  "records": [
    {"patientId":1,"gender":"女","age":61,"province":"湖北","city":"荆州",
     "createTime":"2018-05-08T23:41:35","healthScore":78.5,"healthLevel":"良好"}
  ],
  "total": 100000,
  "page": 1,
  "size": 10
}
~~~

### 3.3 患者详情

请求：GET /api/patients/1

响应 data 包含：patient、diseases、checkups、lifestyle、visits、medications、followups、healthScore。前端用抽屉展示，七个 section 均来自真实表。

### 3.4 趋势

请求：GET /api/trend?grain=year

响应 data：

~~~json
{
  "grain": "year",
  "rows": [
    {"grain":"year","period":"2018","diseaseType":"全部","cases":1975,
     "predictedCases":6976.6,"slope":3902.6548,
     "intercept":-7868580.7262,"r2":0.7361,"trend":"上升","isForecast":0}
  ],
  "forecast": [
    {"period":"2026","predictedCases":38197.8,"isForecast":1}
  ],
  "metrics": {
    "slope":3902.6548,"intercept":-7868580.7262,"r2":0.7361,
    "trend":"上升","algorithm":"最小二乘一元线性回归",
    "trainRange":"2018-2025","forecastRange":"2026-2029"
  }
}
~~~

### 3.5 数据质量

请求：GET /api/data-quality

响应 data.tables 为 7 行，summary 为 totalBefore/totalAfter/totalRemoved/totalIssues/passedTables。

## 4. 参数与校验

- page 最小 1；size 限制 1-100（后端 clamp）。
- keyword 支持患者 ID、省份、城市模糊匹配。
- level 取值：优秀/良好/一般/较差/危险。
- grain 取值：year/month；year 返回年度+月度+预测，month 返回年度+月度。
- factor 取值：smoking/drinking/bmi/exercise/diet。
- type：就诊 type/department/year；用药 top/type/effective/combo。

## 5. 错误示例

~~~json
{"code":404,"message":"患者不存在：999999","data":null}
~~~

## 6. 验证

scripts/check_api.ps1 对 14 个接口做 HTTP 冒烟，实测 14/14 通过，报告 reports/api_test_report.json。
