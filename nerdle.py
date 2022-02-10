#!/usr/bin/env python3

import itertools

letters = "0123456789+-*/="

ops = "+-*/"
eq = "="

digit1 = range(1, 10)
digit2 = range(10, 100)
digit3 = range(100, 1000)
digit4 = range(1000, 10000)

def combine(*components):
	return list(itertools.product(*components))

def filter1(components):
	a = components[0]
	op = components[1]
	b = components[2]
	if op == "+":
		l = a + b
	elif op == "-":
		l = a - b
	elif op == "*":
		l = a * b
	elif op == "/":
		l = a / b
	return l == components[4]

def filter2(components):
	a = components[0]
	b = components[2]
	c = components[4]
	ops = components[1] + components[3]
	if ops == "++":
		l = a + b + c
	elif ops == "+-":
		l = a + b - c
	elif ops == "+*":
		l = a + (b * c)
	elif ops == "+/":
		l = a + (b / c)
	elif ops == "-+":
		l = a - b + c
	elif ops == "--":
		l = a - b - c
	elif ops == "-*":
		l = a - (b * c)
	elif ops == "-/":
		l = a - (b / c)
	elif ops == "*+":
		l = (a * b) + c
	elif ops == "*-":
		l = (a * b) - c
	elif ops == "**":
		l = a * b * c
	elif ops == "*/":
		l = (a * b) / c
	elif ops == "/+":
		l = (a / b) + c
	elif ops == "/-":
		l = (a / b) - c
	elif ops == "/*":
		l = (a / b) * c
	elif ops == "//":
		l = (a / b) / c
	return l == components[6]

equations1 = combine(digit1, ops, digit1, eq, digit4) \
           + combine(digit1, ops, digit2, eq, digit3) \
           + combine(digit1, ops, digit3, eq, digit2) \
           + combine(digit1, ops, digit4, eq, digit1) \
           + combine(digit2, ops, digit1, eq, digit3) \
           + combine(digit2, ops, digit2, eq, digit2) \
           + combine(digit2, ops, digit3, eq, digit1) \
           + combine(digit3, ops, digit1, eq, digit2) \
           + combine(digit3, ops, digit2, eq, digit1) \
           + combine(digit4, ops, digit1, eq, digit1)

equations2 = combine(digit1, ops, digit1, ops, digit1, eq, digit2) \
           + combine(digit1, ops, digit1, ops, digit2, eq, digit1) \
           + combine(digit1, ops, digit2, ops, digit1, eq, digit1) \
           + combine(digit2, ops, digit1, ops, digit1, eq, digit1)

equations1 = list(filter(filter1, equations1))
equations2 = list(filter(filter2, equations2))

for e in equations1:
	s = [str(x) for x in e]
	print("".join(s))

for e in equations2:
        s = [str(x) for x in e]
        print("".join(s))
