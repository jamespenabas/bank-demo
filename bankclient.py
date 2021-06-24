import botbank
import os

bank = botbank.Bank()

items_funcs = {
    "create_account": bank.create_account,
    "check_balance": bank.check_balance,
    "deposit": bank.deposit,
    "withdrawal": bank.withdraw,
    "transfer": bank.transfer,
    "login": bank.login,
    "logout": bank.logout,
    "quit": exit
    }


def menu():
    match = {n: v for n, v in enumerate(items_funcs.keys(), 1)}
    for num, val in enumerate(items_funcs.keys(), 1):
        print(f"Enter {num} to {val}")
    try:
        choice = int(input(">>> "))
    except:
        print('Invalid Input')
    else:
        action = items_funcs[match[choice]]
        os.system('cls')
        action()


if __name__ == "__main__":
    while True:
        menu()