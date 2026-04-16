import matplotlib.pyplot as plt

def calculate_balance(transactions):
    баланс = 0
    for t in transactions:
        if t.тип.lower() == "доход":
            баланс += t.сумма
        else:
            баланс -= t.сумма
    return баланс

def plot_transactions(transactions):
    категории = [t.категория for t in transactions]
    суммы = [t.сумма for t in transactions]
    plt.bar(категории, суммы)
    plt.savefig("график.png")