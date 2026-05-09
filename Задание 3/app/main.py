from __future__ import annotations

import time
from pathlib import Path

import streamlit as st

from agent import analyze_dataset
from config import load_config


ROOT = Path(__file__).resolve().parents[1]
UPLOAD_DIR = ROOT / "outputs" / "uploads"
RUNS_DIR = ROOT / "outputs" / "runs"


st.set_page_config(page_title="LLM Data Analyst Agent", page_icon="📊", layout="wide")

st.title("LLM Data Analyst Agent")
st.caption("Загрузка CSV/Excel, агентный анализ через Python tool и отчет на русском языке.")

with st.sidebar:
    st.subheader("Настройки")
    config = load_config()
    st.write(f"Провайдер: `{config.provider}`")
    st.write(f"Модель: `{config.model}`")
    st.divider()
    st.write("Файл не должен содержать секреты. Текст внутри датасета считается недоверенными данными.")

uploaded = st.file_uploader("Датасет", type=["csv", "xlsx", "xls"])
instruction = st.text_area(
    "Инструкция для анализа",
    value="Проведи EDA, найди ключевые драйверы метрик, аномалии и практические выводы.",
    height=120,
)

run = st.button("Запустить анализ", type="primary", disabled=uploaded is None)

if run and uploaded is not None:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    run_id = time.strftime("%Y%m%d-%H%M%S")
    dataset_path = UPLOAD_DIR / f"{run_id}-{uploaded.name}"
    dataset_path.write_bytes(uploaded.getvalue())
    output_dir = RUNS_DIR / run_id

    with st.status("Агент анализирует датасет через Python tool...", expanded=True) as status:
        try:
            report, chart_paths = analyze_dataset(config, dataset_path, output_dir, instruction)
        except Exception as error:
            status.update(label="Ошибка анализа", state="error")
            st.error(str(error))
        else:
            status.update(label="Анализ завершен", state="complete")
            st.markdown(report)
            if chart_paths:
                st.subheader("Графики")
                columns = st.columns(min(2, len(chart_paths)))
                for index, chart_path in enumerate(chart_paths):
                    with columns[index % len(columns)]:
                        st.image(chart_path, use_column_width=True)
            else:
                st.info("Агент не создал PNG-графики для этого анализа.")
else:
    st.info("Загрузите CSV/Excel и запустите анализ.")
