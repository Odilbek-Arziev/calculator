import streamlit as st
import matplotlib.pyplot as plt


def mortgage_calculator(price, down_payment, annual_rate, monthly_payment=None, years=None):
    loan_amount = price - down_payment
    monthly_rate = annual_rate / 100 / 12

    if years is not None:
        months = years * 12
        payment = loan_amount * (monthly_rate * (1 + monthly_rate) ** months) / ((1 + monthly_rate) ** months - 1)
        payment = round(payment, 2)

        total_paid = payment * months
        overpayment = round(total_paid - loan_amount, 2)

        # график погашения
        balance = loan_amount
        balances = []
        for _ in range(months):
            interest = balance * monthly_rate
            balance = balance + interest - payment
            balances.append(max(balance, 0))

        return payment, f"{years} лет", overpayment, balances

    if monthly_payment is not None:
        if monthly_payment <= loan_amount * monthly_rate:
            return None, None, "Платёж слишком маленький, кредит не погасится.", []

        balance = loan_amount
        months_needed = 0
        total_paid = 0
        balances = []

        while balance > 0 and months_needed < 1000 * 12:
            interest = balance * monthly_rate
            balance = balance + interest - monthly_payment
            balances.append(max(balance, 0))
            total_paid += monthly_payment
            months_needed += 1

        years_needed = months_needed // 12
        months_extra = months_needed % 12
        overpayment = round(total_paid - loan_amount, 2)

        return monthly_payment, f"{years_needed} лет {months_extra} мес.", overpayment, balances

    return None, None, "Укажите либо срок, либо платёж.", []


# --- Streamlit UI ---
st.title("🏦 Ипотечный калькулятор с графиком")

price = st.number_input("Полная стоимость жилья ($)", min_value=1000, step=1000)
down_payment = st.number_input("Первоначальный взнос ($)", min_value=0, step=500)
rate = st.number_input("Годовая ставка (%)", min_value=1.0, step=0.1)

col1, col2 = st.columns(2)
with col1:
    monthly_payment = st.number_input("Желаемый ежемесячный платёж ($)", min_value=0, step=100)
with col2:
    years = st.number_input("Срок кредита (лет)", min_value=0, step=1)

if st.button("Рассчитать"):
    monthly_payment_val = monthly_payment if monthly_payment > 0 else None
    years_val = years if years > 0 else None

    payment, term, overpayment, balances = mortgage_calculator(
        price, down_payment, rate, monthly_payment_val, years_val
    )

    if isinstance(overpayment, str):
        st.error(overpayment)
    else:
        st.success(f"Ежемесячный платёж: **{payment}$**")
        st.info(f"Срок: **{term}**")
        st.warning(f"Переплата: **{overpayment}$**")

        # график остатка долга
        st.subheader("📉 График остатка долга")
        fig, ax = plt.subplots()
        ax.plot(range(1, len(balances) + 1), balances, label="Остаток долга")
        ax.set_xlabel("Месяцы")
        ax.set_ylabel("Остаток ($)")
        ax.set_title("Динамика погашения кредита")
        ax.legend()
        st.pyplot(fig)
