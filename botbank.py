import datetime as dt
import getpass
import hashlib
import logging
import os
import os.path
import pickle
import pyperclip
from random import randint
import re
import termcolor

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s  >>%(levelname)-8s<< %(message)s',
                    datefmt='%m-%d %H:%M')

DIRECTORY = "bank_dat"
info = logging.info
warn = logging.warn


def set_path(directory):
	if not os.path.exists(directory):
		with open(directory, "wb") as f:
			pickle.dump({}, f)
	else:pass

set_path(DIRECTORY)

def load_data():
	with open(DIRECTORY, "rb") as f:
		data = pickle.load(f)
	return data 

class InvalidAmount(Exception):
	pass


class UnregisteredAccount(Exception):
	pass


class Bank:
	__users = load_data()

	def __init__(self):
		self.__logged_in = False
		self.login_msg = "YOU MUST LOGIN!!!"

	#CLASS HOOKS (for class implementation only)

	def __encrypt_pin(self, pin, name):
		hash_string = (pin + name)
		hash_string = hash_string.encode("utf8")
		return hashlib.sha256(hash_string).hexdigest()

	def __get_name(self):
		regez = re.compile(r"((?:\w{2,10})(?: \w{2,10})( \w{2,10})?)")
		name = input("Enter your full names: \n")
		match = regez.search(name)
		try:
			name = match.group()
		except:
			print("No match found\n")
			name = self.__get_name()
		else:
		 validate = re.search(r"[0-9]*", name)
		 if validate is None:
		 	print("Name cannot contain number\n")
		 	name = self.__get_name()
		return name.title()
	
	def __verify(self, pin, name, act_num):
		msg = f"Enter your password for {act_num}: \n"
		for _ in range(3):
			password = getpass.getpass()
			password = self.__encrypt_pin(password, name)
			if password == pin:
				break
		if password == pin:
			return True
		return False
	
	def __hibernate(self, act_num):
		details = Bank.__users[act_num]
		details["wait"] = dt.datetime.now()+dt.timedelta(minutes=30)
		Bank.__users[act_num] = details
		self.__rewrite()
		
	def __isHibernated(self, wait):
		if wait > dt.datetime.now():
			return f"Account hibernated for {wait - dt.datetime.now()}"
		return False
		
	def __user_info(self, act_num):
		return Bank.__users[act_num]
	
	def __update(self, act_num, data):
		Bank.__users[act_num] = data
		self.__rewrite()
	
	def __get_pin(self):
		msg = "Choose a password to secure your account: \n"
		pin = getpass.getpass(prompt=msg)
		while len(pin) < 5:
			warn("Password too short")
			pin = getpass.getpass(prompt=msg)
		return pin
	
	def __gen_number(self):
		while True:
			num = randint(100000000, 999999999)
			num = "0"+str(num)
			if num not in Bank.__users:
				break
		return num
	
	def __create_user(self, act_num, name, pin):
		Bank.__users.update({act_num:{"name":name, "balance":0,"pin":pin, "wait":dt.datetime.now()}})
		self.__rewrite()
	
	def __rewrite(self):
		with open(DIRECTORY, "wb") as f:
			pickle.dump(Bank.__users, f)
	
	def __init(self, act_num, name, balance):
		attributes = ["act_num", "balance", "name"]
		values = [act_num, balance, name]
		for _ in range(len(attributes)):
			super().__setattr__(attributes[_], values[_])
	
	#PUBLIC INTERFACES
	
	def create_account(self):
		msg = "*"*4 +"WELCOME TO BotBank"+"*"*4
		print(msg, end="\n")
		print ("\t<provide your details \n\tto create account>")
		name = self.__get_name()
		act_num = self.__gen_number()
		pin = self.__get_pin()
		dispPin = pin
		pin = self.__encrypt_pin(pin, name)
		self.__create_user(act_num, name, pin)
		os.system('cls')
		print ("Your account has been created\n=====DETAILS=====\n")
		info(f"Name: {name}\nAccount Number: {act_num}\nPassword: {dispPin}\nLogin to access your account\n")
		copy = input('Copy accout number to clipboard? y/n: ')
		copy = copy.lower()
		while copy not in 'yn':
			copy = input('Copy accout number to clipboard? y/n: ')
		if copy == 'y':
			pyperclip.copy(act_num)
	
	def login(self):
		if self.__logged_in is True:
			warn("You are logged in!", 'red')
		msg = "Enter your account number: "
		act_num = input(msg)
		while act_num not in Bank.__users.keys():
			print(f"{act_num} is not registered with BotBank")
			act_num = input(msg)
		user = Bank.__users[act_num]
		name = user["name"]
		wait = user["wait"]
		pin = user["pin"]
		balance = user["balance"]
		b = self.__isHibernated(wait)
		if b:
			return b
		if self.__verify(pin, name, act_num):
			self.__logged_in = True
			self.__init(act_num, name, balance)
			info(f"Welcome back {name}, You are now logged in\n")
		else:
			self.__hibernate(act_num)
			warn("Maximum password attempts exceeded and account has been hibernated for 30 minutes\n")
		
	def deposit(self):
		if not self.__logged_in:
			warn("You must login")
			return
		msg = "Enter amount to deposit: \n"
		try:
			amount = (input(msg))
			amount = int(amount)
		except TypeError:
			raise InvalidAmount(amount) from None
		else:
			if amount > 0:
				self.balance += amount
				data = self.__user_info(self.act_num)
				data["balance"] += amount
				self.__update(self.act_num,data)
				info(f"${amount} has been credited and new balance is ${self.balance}\n")
			else:
				warn("Amount cannot be less than 1")
	
	def transfer(self):
		if not self.__logged_in:
			return self.login_msg
		msg = "Enter amount to transfer: \n"
		try:
			amount = input(msg)
			amount = int(amount)
		except TypeError:
			raise InvalidAmount(amount) from None
		else:
			if amount <= self.balance:
				msg = "Enter recepient account number: \n"
				account = input(msg)
				try:
					recv = Bank.__users[account]
				except KeyError:
					raise UnregisteredAccount(account) from None
				else:
					self.balance -= amount
					details = self.__user_info(self.act_num)
					details["balance"] = self.balance
					self.__update(self.act_num,details)
					recv["balance"] += amount
					self.__update(account, recv)
			else:
				warn("Insufficient Funds\n")
	
	def withdraw(self):
		if not self.__logged_in:
			warn(self.login_msg)
			return
		msg = "Enter amount to withdraw: \n"
		try:
			amount = input(msg)
			amount = int(amount)
		except TypeError:
				raise InvalidAmount(amount) from None
		else:
			if amount < self.balance:
				self.balance -= amount
				update = self.__user_info(self.act_num)
				update["balance"] = self.balance
				self.__update(self.act_num, update)
				info(f"${amount} withdrawn and new balance is ${self.balance}\n")
			else:
				warn("Insufficient funds\n")
	
	def check_balance(self):
		if not self.__logged_in:
			warn(self.login_msg)
			return 0
		info("Available Balance:\n{} ".format(self.balance))
	
	def logout(self):
		if not self.__logged_in:
			return ("YOU ARE NOT LOGGED IN\n")
		self.__logged_in = False
		info(f"Logged out {self.name}")
