import streamlit as st
import pandas as pd
import plotly.express as px


def mortgage_calculator(price, down_payment, annual_rate, monthly_payment=None, years=None):
    loan_amount = price - down_payment
    monthly_rate = annual_rate / 100 / 12
    balances = []
    schedule = []

    if years is not None:
        months = years * 12
        payment = loan_amount * (monthly_rate * (1 + monthly_rate) ** months) / ((1 + monthly_rate) ** months - 1)
        payment = round(payment, 2)
        total_paid = payment * months
        overpayment = round(total_paid - loan_amount, 2)
        balance = loan_amount
        for month in range(1, months + 1):
            interest = round(balance * monthly_rate, 2)
            principal = round(payment - interest, 2)
            balance = round(balance - principal, 2)
            balances.append(balance)
            schedule.append({
                "Месяц": month,
                "Платёж": payment,
                "Проценты": interest,
                "Тело кредита": principal,
                "Остаток долга": max(balance, 0)
            })
        return payment, f"{years} лет", overpayment, balances, pd.DataFrame(schedule)

    if monthly_payment is not None:
        if monthly_payment <= loan_amount * monthly_rate:
            return None, None, "Платёж слишком маленький, кредит не погасится.", [], pd.DataFrame()
        balance = loan_amount
        months_needed = 0
        total_paid = 0
        while balance > 0 and months_needed < 1000 * 12:
            interest = round(balance * monthly_rate, 2)
            principal = round(monthly_payment - interest, 2)
            balance = round(balance - principal, 2)
            balances.append(max(balance, 0))
            schedule.append({
                "Месяц": months_needed + 1,
                "Платёж": monthly_payment,
                "Проценты": interest,
                "Тело кредита": principal,
                "Остаток долга": max(balance, 0)
            })
            total_paid += monthly_payment
            months_needed += 1
        years_needed = months_needed // 12
        months_extra = months_needed % 12
        overpayment = round(total_paid - loan_amount, 2)
        return monthly_payment, f"{years_needed} лет {months_extra} мес.", overpayment, balances, pd.DataFrame(schedule)

    return None, None, "Укажите либо срок, либо платёж.", [], pd.DataFrame()


st.title("🏦 Интерактивный ипотечный калькулятор")

currency = st.radio("Выберите валюту", ("USD", "UZS"))

if currency == "UZS":
    usd_to_uzs = st.number_input("Введите курс USD к UZS", min_value=1000, value=11500, step=100)
else:
    usd_to_uzs = 1

price_input = st.number_input(
    f"Полная стоимость жилья ({currency})",
    min_value=1000 if currency == "USD" else 1_000_000,
    step=1000 if currency == "USD" else 1_000_000,
    value=50_000 if currency == "USD" else 50_000 * usd_to_uzs
)
down_payment_input = st.number_input(
    f"Первоначальный взнос ({currency})",
    min_value=0,
    step=1000 if currency == "USD" else 1_000_000,
    value=10_000 if currency == "USD" else 10_000 * usd_to_uzs
)

years_input = st.number_input("Срок кредита (лет)", min_value=1, step=1, value=10)

price_usd = price_input / usd_to_uzs
down_payment_usd = down_payment_input / usd_to_uzs

monthly_rate = st.number_input("Годовая ставка (%)", min_value=1.0, step=0.1, value=10.0) / 100 / 12
months_total = years_input * 12
default_payment = round(
    (price_usd - down_payment_usd) * (monthly_rate * (1 + monthly_rate) ** months_total) / (
            (1 + monthly_rate) ** months_total - 1), 2
)
min_payment = round((price_usd - down_payment_usd) * monthly_rate * 1.01, 2)

col1, col2 = st.columns(2)
with col1:
    monthly_slider = st.slider(
        f"Ползунок ежемесячного платежа ({currency})",
        min_value=int(min_payment * usd_to_uzs),
        max_value=int(default_payment * 3 * usd_to_uzs),
        value=int(default_payment * usd_to_uzs),
        step=50 if currency == "USD" else 50_000
    )
with col2:
    monthly_input = st.number_input(
        f"Точный ежемесячный платёж ({currency})",
        min_value=int(min_payment * usd_to_uzs),
        max_value=int(default_payment * 3 * usd_to_uzs),
        value=int(monthly_slider),
        step=50 if currency == "USD" else 50_000
    )

monthly_usd = monthly_input / usd_to_uzs

payment, term, overpayment, balances, schedule = mortgage_calculator(
    price_usd, down_payment_usd, monthly_rate * 12 * 100, monthly_payment=monthly_usd
)

payment_display = round(payment * usd_to_uzs, 2) if payment else 0
overpayment_display = round(overpayment * usd_to_uzs, 2) if overpayment else 0
balances_display = [round(b * usd_to_uzs, 2) for b in balances]
schedule_display = schedule.copy()
for col in ["Платёж", "Проценты", "Тело кредита", "Остаток долга"]:
    schedule_display[col] = schedule_display[col] * usd_to_uzs

st.success(f"Ежемесячный платёж: **{payment_display} {currency}**")
st.info(f"Срок: **{term}**")
st.warning(f"Переплата: **{overpayment_display} {currency}**")

if balances:
    st.subheader("📉 График остатка долга")
    st.line_chart(pd.DataFrame({"Остаток долга": balances_display}))

    st.subheader("📊 Таблица платежей по месяцам")
    st.dataframe(schedule_display)

    st.subheader("💰 Распределение переплаты")
    pie_data = pd.DataFrame({
        "Категория": ["Тело кредита", "Переплата процентов"],
        "Сумма": [price_input - down_payment_input, overpayment_display]
    })
    fig = px.pie(pie_data, names='Категория', values='Сумма', title='Доля переплаты и основного долга')
    st.plotly_chart(fig)
