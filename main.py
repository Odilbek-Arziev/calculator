import streamlit as st
import pandas as pd

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


# --- Streamlit UI ---
st.title("🏦 Интерактивный ипотечный калькулятор")

price = st.number_input("Полная стоимость жилья ($)", min_value=1000, step=1000, value=50000)
down_payment = st.number_input("Первоначальный взнос ($)", min_value=0, step=500, value=10000)
rate = st.number_input("Годовая ставка (%)", min_value=1.0, step=0.1, value=10.0)
years = st.number_input("Срок кредита (лет)", min_value=1, step=1, value=10)

# Рассчитываем минимальный и рекомендованный ежемесячный платеж
loan_amount = price - down_payment
monthly_rate = rate / 100 / 12
months = years * 12
min_payment = round(loan_amount * monthly_rate * 1.01, 2)  # чуть больше процентов
default_payment = round(loan_amount * (monthly_rate * (1 + monthly_rate) ** months) / ((1 + monthly_rate) ** months - 1), 2)

st.subheader("Настройка ежемесячного платежа")
monthly_payment = st.slider(
    "Ежемесячный платёж ($)",
    min_value=int(min_payment),
    max_value=int(default_payment*3),
    value=int(default_payment),
    step=50
)

# Автопересчет
payment, term, overpayment, balances, schedule = mortgage_calculator(
    price, down_payment, rate, monthly_payment=monthly_payment
)

st.success(f"Ежемесячный платёж: **{payment}$**")
st.info(f"Срок: **{term}**")
st.warning(f"Переплата: **{overpayment}$**")

if balances:
    st.subheader("📉 График остатка долга")
    st.line_chart(pd.DataFrame({"Остаток долга": balances}))

    st.subheader("📊 Таблица платежей по месяцам")
    st.dataframe(schedule)

    st.subheader("💰 Распределение переплаты")
    total_principal = price - down_payment
    pie_data = pd.DataFrame({
        "Сумма": [total_principal, overpayment],
        "Категория": ["Тело кредита", "Переплата процентов"]
    })
    st.pyplot(pie_data.plot.pie(y='Сумма', labels=pie_data['Категория'], autopct='%1.1f%%', legend=False).get_figure())
