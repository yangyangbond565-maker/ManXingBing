# -*- coding: utf-8 -*-
"""生成 7 张业务表的可复现模拟数据。

统计口径（已按飞书原文核实）：
  patient_info = 100,000 人；其余 6 张表按患者一对多生成。
  “10 万条”指患者人数，而不是七张表记录数简单相加。

所有姓名/证件号/手机号均为程序生成的虚构值，不对应真实个人。
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import time
from datetime import date, datetime, timedelta
from pathlib import Path

from .config import GENERATED_DIR, PATIENT_COUNT, RANDOM_SEED, ensure_dirs

PROVINCES_CITIES = {
    "北京": ["东城区", "西城区", "朝阳区", "海淀区"],
    "上海": ["浦东新区", "徐汇区", "静安区", "黄浦区"],
    "广东": ["广州", "深圳", "东莞", "佛山"],
    "浙江": ["杭州", "宁波", "温州", "嘉兴"],
    "江苏": ["南京", "苏州", "无锡", "常州"],
    "四川": ["成都", "绵阳", "德阳", "宜宾"],
    "湖北": ["武汉", "宜昌", "襄阳", "荆州"],
    "湖南": ["长沙", "株洲", "湘潭", "衡阳"],
    "山东": ["济南", "青岛", "烟台", "潍坊"],
    "河南": ["郑州", "洛阳", "开封", "许昌"],
    "河北": ["石家庄", "唐山", "保定", "廊坊"],
    "福建": ["福州", "厦门", "泉州", "漳州"],
    "安徽": ["合肥", "芜湖", "蚌埠", "马鞍山"],
    "陕西": ["西安", "咸阳", "宝鸡", "渭南"],
    "辽宁": ["沈阳", "大连", "鞍山", "抚顺"],
    "重庆": ["渝中区", "江北区", "沙坪坝", "九龙坡"],
}

DISEASES = {
    "高血压": (["原发性高血压", "继发性高血压", "高血压性心脏病", "高血压肾病"], 0.27, ["心内科", "全科"]),
    "糖尿病": (["1型糖尿病", "2型糖尿病", "糖尿病肾病", "糖尿病视网膜病变"], 0.20, ["内分泌科", "全科"]),
    "冠心病": (["稳定性心绞痛", "不稳定性心绞痛", "心肌梗死", "缺血性心肌病"], 0.14, ["心内科"]),
    "脑卒中": (["缺血性脑卒中", "出血性脑卒中", "脑梗死", "脑出血后遗症"], 0.10, ["神经内科"]),
    "慢阻肺": (["慢性支气管炎", "肺气肿", "支气管哮喘", "支气管扩张"], 0.09, ["呼吸科"]),
    "慢性肾病": (["慢性肾小球肾炎", "糖尿病肾病", "高血压肾病", "慢性肾功能不全"], 0.07, ["肾内科"]),
    "慢性肝病": (["脂肪肝", "肝硬化", "慢性乙肝", "药物性肝损伤"], 0.05, ["消化内科"]),
    "骨质疏松": (["原发性骨质疏松", "继发性骨质疏松", "骨质减少症"], 0.04, ["骨科"]),
    "类风湿": (["类风湿关节炎", "类风湿性心脏病", "类风湿性肺病"], 0.02, ["风湿免疫科"]),
    "抑郁症": (["轻度抑郁", "中度抑郁", "重度抑郁", "双相情感障碍"], 0.02, ["精神科"]),
}

DRUGS = {
    "高血压": [("硝苯地平", "钙通道阻滞剂"), ("氨氯地平", "钙通道阻滞剂"), ("缬沙坦", "ARB类"),
             ("厄贝沙坦", "ARB类"), ("美托洛尔", "β受体阻滞剂"), ("氢氯噻嗪", "利尿剂"),
             ("卡托普利", "ACEI类"), ("依那普利", "ACEI类")],
    "糖尿病": [("二甲双胍", "双胍类"), ("格列美脲", "磺脲类"), ("阿卡波糖", "α-糖苷酶抑制剂"),
             ("西格列汀", "DPP-4抑制剂"), ("利拉鲁肽", "GLP-1受体激动剂"),
             ("达格列净", "SGLT-2抑制剂"), ("胰岛素", "胰岛素类"), ("吡格列酮", "噻唑烷二酮类")],
    "冠心病": [("阿司匹林", "抗血小板药"), ("氯吡格雷", "抗血小板药"), ("阿托伐他汀", "他汀类"),
             ("瑞舒伐他汀", "他汀类"), ("硝酸甘油", "硝酸酯类"), ("美托洛尔", "β受体阻滞剂")],
    "脑卒中": [("阿司匹林", "抗血小板药"), ("华法林", "抗凝药"), ("丁苯酞", "脑血管扩张剂"),
             ("依达拉奉", "脑保护剂"), ("阿托伐他汀", "他汀类"), ("氯吡格雷", "抗血小板药")],
    "慢阻肺": [("布地奈德", "糖皮质激素"), ("沙美特罗", "β2受体激动剂"), ("噻托溴铵", "抗胆碱药"),
             ("茶碱", "甲基黄嘌呤类")],
    "慢性肾病": [("厄贝沙坦", "ARB类"), ("呋塞米", "利尿剂"), ("促红细胞生成素", "促红素"), ("碳酸钙", "钙剂")],
    "慢性肝病": [("多烯磷脂酰胆碱", "肝细胞保护剂"), ("甘草酸二铵", "抗炎保肝药"),
              ("水飞蓟素", "肝细胞保护剂"), ("恩替卡韦", "抗病毒药")],
    "骨质疏松": [("阿仑膦酸钠", "双膦酸盐类"), ("碳酸钙", "钙剂"), ("骨化三醇", "维生素D类")],
    "类风湿": [("甲氨蝶呤", "免疫抑制剂"), ("来氟米特", "免疫抑制剂"), ("塞来昔布", "COX-2抑制剂"),
             ("羟氯喹", "抗疟药")],
    "抑郁症": [("舍曲林", "SSRI类"), ("氟西汀", "SSRI类"), ("帕罗西汀", "SSRI类"), ("文拉法辛", "SNRI类")],
}

HOSPITALS = [
    "北京协和医院", "上海瑞金医院", "广州中山医院", "四川华西医院",
    "武汉同济医院", "南京鼓楼医院", "杭州邵逸夫医院", "长沙湘雅医院",
    "市第一人民医院", "市第二人民医院", "市第三人民医院",
    "市中医院", "市中心医院", "县人民医院",
]
DOSAGES = ["每日1次,每次1片", "每日2次,每次1片", "每日3次,每次1片", "每日1次,每次2片", "必要时服用", "每日1次,每次半片"]
ADVICES = [
    "继续当前用药方案，注意饮食控制",
    "建议增加运动量，每周至少3次有氧运动",
    "血压控制良好，继续观察",
    "血糖偏高，建议调整饮食结构",
    "建议戒烟限酒，规律作息",
    "药物效果良好，继续服用",
    "建议定期复查肝肾功能和血脂",
    "注意控制体重，BMI超标",
    "建议增加蔬菜水果摄入，减少盐分",
    "需要调整用药方案，请按时复诊",
]
AREA_CODES = ["1101", "3101", "4401", "3301", "3201", "5101", "4201", "4301",
              "3701", "4101", "1301", "3501", "3401", "6101", "2101", "5001"]

FILES = {
    "patient_info": ["patient_id", "gender", "age", "province", "city", "id_number", "phone", "create_time"],
    "disease_record": ["patient_id", "disease_type", "disease_name", "diagnose_date", "severity", "doctor_id", "hospital"],
    "health_checkup": ["patient_id", "checkup_date", "sbp", "dbp", "fasting_glucose", "hba1c", "tc", "tg",
                       "hdl", "ldl", "bmi", "heart_rate", "creatinine", "uric_acid"],
    "lifestyle": ["patient_id", "smoking_status", "smoking_amount", "drinking_status", "exercise_freq",
                  "sleep_hours", "diet_pattern"],
    "visit_record": ["patient_id", "visit_date", "visit_type", "hospital", "department", "diagnosis",
                     "cost", "insurance_pay", "self_pay", "stay_days"],
    "medication_record": ["patient_id", "drug_name", "drug_type", "dosage", "start_date", "end_date",
                          "cost", "is_effective"],
    "follow_up": ["patient_id", "follow_date", "follow_type", "symptom_status", "medication_adherence",
                  "doctor_advice", "next_follow_date"],
}

DISEASE_WEIGHTS = [v[1] for v in DISEASES.values()]


def rand_date(start: date, end: date, rng: random.Random) -> date:
    return start + timedelta(days=rng.randint(0, (end - start).days))


def synthetic_id(patient_id: int, age: int, rng: random.Random) -> str:
    """18 位虚构证件号：4 位地区 + 8 位出生日期 + 5 位序号 + 1 位校验字符。"""
    birth_year = date.today().year - age
    month = rng.randint(1, 12)
    day = rng.randint(1, 28)
    area = AREA_CODES[patient_id % len(AREA_CODES)]
    return f"{area}{birth_year:04d}{month:02d}{day:02d}{patient_id:05d}{'X' if patient_id % 11 == 0 else str(patient_id % 10)}"


def synthetic_phone(patient_id: int) -> str:
    prefix = ["138", "139", "150", "151", "186", "187", "135", "136"][patient_id % 8]
    return prefix + f"{patient_id:08d}"


def make_patient(patient_id: int, rng: random.Random):
    gender = "男" if rng.random() < 0.505 else "女"
    # 中老年为主，符合社区慢病管理场景
    age = int(min(90, max(25, rng.gauss(62, 13))))
    province = rng.choice(list(PROVINCES_CITIES))
    city = rng.choice(PROVINCES_CITIES[province])
    create = datetime(2018, 1, 1) + timedelta(
        days=rng.randint(0, (date(2022, 12, 31) - date(2018, 1, 1)).days),
        seconds=rng.randint(0, 86399),
    )
    return {
        "patient_id": patient_id, "gender": gender, "age": age, "province": province, "city": city,
        "id_number": synthetic_id(patient_id, age, rng), "phone": synthetic_phone(patient_id),
        "create_time": create.strftime("%Y-%m-%d %H:%M:%S"),
    }


def choose_diseases(patient_id: int, rng: random.Random):
    count = rng.choices([1, 2, 3], weights=[50, 35, 15])[0]
    types = rng.choices(list(DISEASES), weights=DISEASE_WEIGHTS, k=count * 2)
    unique = []
    for t in types:
        if t not in unique:
            unique.append(t)
        if len(unique) == count:
            break
    while len(unique) < count:
        t = rng.choice(list(DISEASES))
        if t not in unique:
            unique.append(t)
    return unique


def make_lifestyle(patient_id: int, diseases: set[str], rng: random.Random):
    smoking_p = 0.22
    if diseases & {"慢阻肺", "冠心病", "脑卒中"}:
        smoking_p += 0.18
    smoking = rng.choices(["从不", "已戒", "在吸"], weights=[1 - smoking_p - 0.18, 0.18, smoking_p])[0]
    amount = rng.randint(5, 30) if smoking == "在吸" else 0
    drink_p = 0.28 + (0.12 if "慢性肝病" in diseases else 0)
    drinking = rng.choices(["从不", "已戒", "在饮"], weights=[1 - drink_p - 0.15, 0.15, drink_p])[0]
    exercise = rng.choices(["无", "偶尔", "经常"], weights=[0.30, 0.42, 0.28])[0]
    sleep_hours = round(rng.uniform(4.5, 9.0), 1)
    diet = rng.choices(["清淡", "正常", "重口味"], weights=[0.28, 0.47, 0.25])[0]
    return {
        "patient_id": patient_id, "smoking_status": smoking, "smoking_amount": amount,
        "drinking_status": drinking, "exercise_freq": exercise, "sleep_hours": sleep_hours,
        "diet_pattern": diet,
    }


def make_checkups(patient_id: int, diseases: set[str], lifestyle: dict, rng: random.Random):
    rows = []
    for _ in range(rng.randint(2, 4)):
        d = rand_date(date(2021, 1, 1), date(2025, 12, 31), rng)
        htn = "高血压" in diseases or "慢性肾病" in diseases
        dm = "糖尿病" in diseases
        if htn and rng.random() < 0.70:
            sbp = rng.randint(140, 195)
            dbp = rng.randint(85, min(120, sbp - 20))
        elif htn:
            sbp = rng.randint(125, 145)
            dbp = rng.randint(75, min(95, sbp - 20))
        else:
            sbp = rng.randint(100, 135)
            dbp = rng.randint(62, min(88, sbp - 20))
        if dm and rng.random() < 0.72:
            fg = round(rng.uniform(7.0, 15.0), 2)
            hba1c = round(rng.uniform(6.8, 12.0), 2)
        else:
            fg = round(rng.uniform(4.0, 6.4), 2)
            hba1c = round(rng.uniform(4.5, 6.2), 2)
        bmi_base = 26.5 if lifestyle["diet_pattern"] == "重口味" else 23.5
        if lifestyle["exercise_freq"] == "经常":
            bmi_base -= 1.5
        bmi = round(min(38.0, max(17.0, rng.gauss(bmi_base, 3.2))), 2)
        tc = round(rng.uniform(3.8, 7.8), 2)
        tg = round(rng.uniform(0.8, 4.8), 2)
        hdl = round(rng.uniform(0.8, 2.2), 2)
        ldl = round(rng.uniform(1.8, 5.6), 2)
        hr = rng.randint(55, 112)
        creatinine = round(rng.uniform(45, 170) if "慢性肾病" in diseases else rng.uniform(40, 110), 2)
        uric = round(rng.uniform(240, 580) if "慢性肾病" in diseases else rng.uniform(180, 480), 2)
        rows.append({
            "patient_id": patient_id, "checkup_date": d.isoformat(), "sbp": sbp, "dbp": dbp,
            "fasting_glucose": fg, "hba1c": hba1c, "tc": tc, "tg": tg, "hdl": hdl, "ldl": ldl,
            "bmi": bmi, "heart_rate": hr, "creatinine": creatinine, "uric_acid": uric,
        })
    return rows


def make_visits(patient_id: int, disease_names: list[str], types: list[str], rng: random.Random):
    rows = []
    for _ in range(rng.randint(3, 8)):
        vt = rng.choices(["门诊", "急诊", "住院"], weights=[60, 15, 25])[0]
        d = rand_date(date(2021, 1, 1), date(2025, 12, 31), rng)
        if vt == "门诊":
            cost, stay, rate = round(rng.uniform(100, 2000), 2), 0, rng.uniform(0.35, 0.65)
        elif vt == "急诊":
            cost, stay, rate = round(rng.uniform(500, 5000), 2), 0, rng.uniform(0.25, 0.55)
        else:
            cost, stay, rate = round(rng.uniform(5000, 80000), 2), rng.randint(3, 30), rng.uniform(0.55, 0.85)
        insurance = round(cost * rate, 2)
        dept = rng.choice(DISEASES[types[0]][2])
        rows.append({
            "patient_id": patient_id, "visit_date": d.isoformat(), "visit_type": vt,
            "hospital": rng.choice(HOSPITALS), "department": dept,
            "diagnosis": rng.choice(disease_names), "cost": cost,
            "insurance_pay": insurance, "self_pay": round(cost - insurance, 2), "stay_days": stay,
        })
    return rows


def make_medications(patient_id: int, types: list[str], rng: random.Random):
    rows = []
    pool = []
    for t in types:
        pool.extend(DRUGS.get(t, []))
    if not pool:
        return rows
    for _ in range(rng.randint(3, 8)):
        drug, dtype = rng.choice(pool)
        start = rand_date(date(2021, 1, 1), date(2025, 6, 30), rng)
        end = start + timedelta(days=rng.randint(7, 365))
        if end > date(2025, 12, 31):
            end = date(2025, 12, 31)
        rows.append({
            "patient_id": patient_id, "drug_name": drug, "drug_type": dtype,
            "dosage": rng.choice(DOSAGES), "start_date": start.isoformat(), "end_date": end.isoformat(),
            "cost": round(rng.uniform(20, 500), 2),
            "is_effective": rng.choices(["是", "否"], weights=[0.78, 0.22])[0],
        })
    return rows


def make_followups(patient_id: int, rng: random.Random):
    rows = []
    for _ in range(rng.randint(2, 4)):
        fd = rand_date(date(2021, 1, 1), date(2025, 10, 31), rng)
        nxt = fd + timedelta(days=rng.choice([30, 60, 90]))
        rows.append({
            "patient_id": patient_id, "follow_date": fd.isoformat(),
            "follow_type": rng.choices(["电话", "面访", "线上"], weights=[0.40, 0.40, 0.20])[0],
            "symptom_status": rng.choices(["好转", "稳定", "加重"], weights=[0.30, 0.50, 0.20])[0],
            "medication_adherence": rng.choices(["好", "一般", "差"], weights=[0.50, 0.35, 0.15])[0],
            "doctor_advice": rng.choice(ADVICES), "next_follow_date": nxt.isoformat(),
        })
    return rows


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def generate(patient_count: int = PATIENT_COUNT, seed: int = RANDOM_SEED, out_dir: Path = GENERATED_DIR) -> dict:
    rng = random.Random(seed)
    ensure_dirs()
    out_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    counts = {name: 0 for name in FILES}
    paths = {name: out_dir / f"{name}.csv" for name in FILES}
    handles = {name: paths[name].open("w", encoding="utf-8", newline="") for name in FILES}
    writers = {name: csv.DictWriter(handles[name], fieldnames=FILES[name], lineterminator="\n") for name in FILES}
    for name in FILES:
        writers[name].writeheader()

    for pid in range(1, patient_count + 1):
        patient = make_patient(pid, rng)
        writers["patient_info"].writerow(patient)
        counts["patient_info"] += 1

        types = choose_diseases(pid, rng)
        disease_names = []
        for dtype in types:
            names = DISEASES[dtype][0]
            name = rng.choice(names)
            disease_names.append(name)
            # 年度确诊量整体呈上升趋势，保证趋势预测有可解释的历史序列
            year = rng.choices(range(2018, 2026), weights=[6, 7, 8, 9, 10, 11, 12, 13])[0]
            diag = rand_date(date(year, 1, 1), date(year, 12, 31), rng)
            created = datetime.strptime(patient["create_time"], "%Y-%m-%d %H:%M:%S").date()
            if diag <= created:
                diag = created + timedelta(days=rng.randint(30, 180))
            if diag > date(2025, 12, 31):
                diag = date(2025, 12, 31)
            writers["disease_record"].writerow({
                "patient_id": pid, "disease_type": dtype, "disease_name": name,
                "diagnose_date": diag.isoformat(),
                "severity": rng.choices(["轻度", "中度", "重度"], weights=[40, 40, 20])[0],
                "doctor_id": rng.randint(1001, 1200), "hospital": rng.choice(HOSPITALS),
            })
            counts["disease_record"] += 1

        lifestyle = make_lifestyle(pid, set(types), rng)
        writers["lifestyle"].writerow(lifestyle)
        counts["lifestyle"] += 1

        for row in make_checkups(pid, set(types), lifestyle, rng):
            writers["health_checkup"].writerow(row)
            counts["health_checkup"] += 1
        for row in make_visits(pid, disease_names, types, rng):
            writers["visit_record"].writerow(row)
            counts["visit_record"] += 1
        for row in make_medications(pid, types, rng):
            writers["medication_record"].writerow(row)
            counts["medication_record"] += 1
        for row in make_followups(pid, rng):
            writers["follow_up"].writerow(row)
            counts["follow_up"] += 1

        if pid % 10000 == 0:
            print(f"  generated {pid:,}/{patient_count:,} patients, elapsed {time.time()-t0:.1f}s", flush=True)

    for h in handles.values():
        h.close()
    elapsed = time.time() - t0
    manifest = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "seed": seed,
        "patient_count": patient_count,
        "elapsed_seconds": round(elapsed, 2),
        "tables": {},
        "note": "10万统计口径为 patient_info 患者人数；其余表按一对多关系生成。",
    }
    for name in FILES:
        manifest["tables"][name] = {
            "rows": counts[name],
            "bytes": paths[name].stat().st_size,
            "sha256": sha256_file(paths[name]),
            "columns": FILES[name],
        }
    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="生成社区慢性病模拟数据")
    parser.add_argument("--patients", type=int, default=PATIENT_COUNT)
    parser.add_argument("--seed", type=int, default=RANDOM_SEED)
    parser.add_argument("--out", type=Path, default=GENERATED_DIR)
    args = parser.parse_args()
    generate(args.patients, args.seed, args.out)


if __name__ == "__main__":
    main()
