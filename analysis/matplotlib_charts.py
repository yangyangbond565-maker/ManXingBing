# -*- coding: utf-8 -*-
"""基于 MySQL ADS 结果生成 8 张 Matplotlib 分析图（真实数据，不写死数值）。"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import font_manager

from chronic_disease.config import ADS_DIR, DB_CONFIG, PROJECT_ROOT, ensure_dirs
from chronic_disease.db import connect

OUT = PROJECT_ROOT / "analysis" / "output"
OUT.mkdir(parents=True, exist_ok=True)

FONT_CANDIDATES = [
    r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\msyhbd.ttc",
    r"C:\Windows\Fonts\simhei.ttf", r"C:\Windows\Fonts\simsun.ttc",
]
font_path = next((p for p in FONT_CANDIDATES if Path(p).exists()), None)
if font_path:
    font_manager.fontManager.addfont(font_path)
    plt.rcParams["font.family"] = font_manager.FontProperties(fname=font_path).get_name()
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["figure.dpi"] = 120


def read(sql: str) -> pd.DataFrame:
    conn = connect()
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            cols = [d[0] for d in cur.description]
            rows = cur.fetchall()
        return pd.DataFrame(rows, columns=cols)
    finally:
        conn.close()


def save(fig, name: str, table: pd.DataFrame):
    fig.tight_layout()
    fig.savefig(OUT / f"{name}.png", bbox_inches="tight", facecolor="white")
    plt.close(fig)
    table.to_csv(OUT / f"{name}.csv", index=False, encoding="utf-8-sig")
    print("saved", name, len(table))


def chart_disease():
    df = read("SELECT disease_type, patient_count, severe_rate FROM ads_disease_dist ORDER BY patient_count DESC")
    fig, ax = plt.subplots(figsize=(10, 5.6))
    colors = plt.cm.Blues([0.45 + 0.5 * i / max(1, len(df)-1) for i in range(len(df))])[::-1]
    bars = ax.barh(df["disease_type"][::-1], df["patient_count"][::-1], color=colors)
    ax.set_title("图1  慢性病类型分布（按患者人数）", fontsize=15, fontweight="bold")
    ax.set_xlabel("患者人数")
    ax.grid(axis="x", alpha=.2)
    for b, v in zip(bars, df["patient_count"][::-1]):
        ax.text(v + 300, b.get_y() + b.get_height()/2, f"{int(v):,}", va="center", fontsize=9)
    ax.set_xlim(0, df["patient_count"].max() * 1.15)
    save(fig, "fig1_disease_distribution", df)


def chart_profile():
    gender = read("SELECT dimension_value, patient_count FROM ads_patient_profile WHERE dimension_type='gender'")
    age = read("SELECT dimension_value, patient_count FROM ads_patient_profile WHERE dimension_type='age'")
    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    axes[0].pie(gender["patient_count"], labels=gender["dimension_value"], autopct="%1.1f%%",
                colors=["#2563eb", "#f472b6"], startangle=90,
                wedgeprops={"width": .42, "edgecolor": "white"})
    axes[0].set_title("性别构成", fontsize=13, fontweight="bold")
    order = ["青年(<30)", "中青年(30-44)", "中年(45-59)", "中老年(60-74)", "老年(75+)"]
    age["dimension_value"] = pd.Categorical(age["dimension_value"], order, ordered=True)
    age = age.sort_values("dimension_value")
    axes[1].bar(age["dimension_value"], age["patient_count"], color="#06b6d4")
    axes[1].set_title("年龄分组", fontsize=13, fontweight="bold")
    axes[1].tick_params(axis="x", rotation=20)
    for x, v in zip(range(len(age)), age["patient_count"]):
        axes[1].text(x, v + 300, f"{int(v):,}", ha="center", fontsize=8)
    fig.suptitle("图2  患者人群画像", fontsize=15, fontweight="bold")
    save(fig, "fig2_patient_profile", pd.concat([gender.assign(group="gender"), age.assign(group="age")]))


def chart_severity():
    df = read("SELECT disease_type, severity, record_count FROM ads_severity")
    pivot = df.pivot(index="disease_type", columns="severity", values="record_count").fillna(0)
    for c in ["轻度", "中度", "重度"]:
        if c not in pivot: pivot[c] = 0
    pivot = pivot[["轻度", "中度", "重度"]]
    fig, ax = plt.subplots(figsize=(10, 5.6))
    pivot.plot(kind="barh", stacked=True, ax=ax, color=["#10b981", "#f59e0b", "#ef4444"])
    ax.set_title("图3  各疾病严重程度构成", fontsize=15, fontweight="bold")
    ax.set_xlabel("诊断记录数")
    ax.grid(axis="x", alpha=.2)
    ax.legend(title="严重程度", loc="lower right")
    save(fig, "fig3_severity", df)


def chart_risk():
    df = read("""SELECT factor_type, factor_value, SUM(patient_count) patient_count
                  FROM ads_risk_factor GROUP BY factor_type, factor_value""")
    smoke = df[df.factor_type == "smoking"]
    bmi = df[df.factor_type == "bmi"]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8))
    axes[0].bar(smoke["factor_value"], smoke["patient_count"], color=["#94a3b8", "#38bdf8", "#ef4444"])
    axes[0].set_title("吸烟状态（按疾病关联人次）", fontsize=12, fontweight="bold")
    for x, v in zip(range(len(smoke)), smoke["patient_count"]):
        axes[0].text(x, v + 1000, f"{int(v):,}", ha="center", fontsize=8)
    axes[1].bar(bmi["factor_value"], bmi["patient_count"], color="#8b5cf6")
    axes[1].set_title("BMI 分级（体检记录）", fontsize=12, fontweight="bold")
    for x, v in zip(range(len(bmi)), bmi["patient_count"]):
        axes[1].text(x, v + 1000, f"{int(v):,}", ha="center", fontsize=8)
    fig.suptitle("图4  风险因素关联", fontsize=15, fontweight="bold")
    save(fig, "fig4_risk_factor", df)


def chart_visit():
    df = read("SELECT dimension_value, visit_count, avg_cost FROM ads_visit_analysis WHERE analysis_type='type'")
    fig, ax1 = plt.subplots(figsize=(9, 5))
    bars = ax1.bar(df["dimension_value"], df["visit_count"], color=["#2563eb", "#f59e0b", "#ef4444"])
    ax1.set_ylabel("就诊次数")
    ax1.set_title("图5  就诊类型与次均费用", fontsize=15, fontweight="bold")
    for b, v in zip(bars, df["visit_count"]):
        ax1.text(b.get_x()+b.get_width()/2, v+3000, f"{int(v):,}", ha="center", fontsize=9)
    ax2 = ax1.twinx()
    ax2.plot(df["dimension_value"], df["avg_cost"], color="#0f172a", marker="o", linewidth=2)
    ax2.set_ylabel("次均费用（元）")
    ax1.grid(axis="y", alpha=.2)
    save(fig, "fig5_visit_cost", df)


def chart_medication():
    df = read("SELECT dimension_value drug_name, usage_count FROM ads_medication_analysis WHERE analysis_type='top' ORDER BY rank_no")
    fig, ax = plt.subplots(figsize=(10, 5.6))
    bars = ax.barh(df["drug_name"][::-1], df["usage_count"][::-1], color="#10b981")
    ax.set_title("图6  常用药物 TOP 20", fontsize=15, fontweight="bold")
    ax.set_xlabel("用药记录数")
    for b, v in zip(bars, df["usage_count"][::-1]):
        ax.text(v+100, b.get_y()+b.get_height()/2, f"{int(v):,}", va="center", fontsize=8)
    ax.grid(axis="x", alpha=.2)
    save(fig, "fig6_drug_top20", df)


def chart_trend():
    df = read("SELECT grain, period, cases, predicted_cases, is_forecast FROM ads_trend WHERE grain='year' AND disease_type='全部' ORDER BY period")
    actual = df[df.is_forecast == 0]
    pred = df[df.is_forecast == 1]
    fig, ax = plt.subplots(figsize=(10, 5.4))
    ax.plot(actual["period"], actual["cases"], marker="o", linewidth=2.5, color="#2563eb", label="实际病例")
    ax.plot(pd.concat([actual, pred])["period"], pd.concat([actual, pred])["predicted_cases"],
            linestyle="--", marker=".", color="#f59e0b", label="回归拟合 / 预测")
    ax.axvline(len(actual)-0.5, color="#94a3b8", linestyle=":", linewidth=1)
    ax.set_title("图7  年度确诊趋势与 2026-2029 线性预测", fontsize=15, fontweight="bold")
    ax.set_ylabel("确诊病例数")
    ax.legend()
    ax.grid(alpha=.2)
    save(fig, "fig7_trend_forecast", df)


def chart_health():
    levels = read("SELECT level, patient_count FROM ads_health_level ORDER BY sort_no")
    scores = read("SELECT health_score FROM ads_health_score")
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.8))
    axes[0].bar(levels["level"], levels["patient_count"],
                color=["#10b981", "#2563eb", "#f59e0b", "#fb7185", "#ef4444"])
    axes[0].set_title("健康等级分布", fontsize=12, fontweight="bold")
    for x, v in zip(range(len(levels)), levels["patient_count"]):
        axes[0].text(x, v+500, f"{int(v):,}", ha="center", fontsize=8)
    axes[1].hist(scores["health_score"], bins=20, color="#06b6d4", edgecolor="white")
    axes[1].set_title("健康评分分布（0-100）", fontsize=12, fontweight="bold")
    axes[1].set_xlabel("health_score")
    fig.suptitle("图8  健康评分模型结果", fontsize=15, fontweight="bold")
    save(fig, "fig8_health_score", pd.concat([levels.assign(kind="level"), scores.assign(kind="score")]))


def main():
    ensure_dirs()
    chart_disease(); chart_profile(); chart_severity(); chart_risk()
    chart_visit(); chart_medication(); chart_trend(); chart_health()
    print("all charts written to", OUT)


if __name__ == "__main__":
    main()
