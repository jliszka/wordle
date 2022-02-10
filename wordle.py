#!/usr/bin/env python3

from collections import defaultdict
from enum import Enum
import math
import re
import sys

class Mode(Enum):
	play = 1
	adversary = 2
	interactive = 3

def readwords(fn):
	words = []
	total = 0
	f = open(fn)
	lines = f.readlines()
	for line in lines:
		parts = line.rstrip().split(' ')
		freq = int(parts[1]) if len(parts) > 1 else 1
		total += freq
		words.append((parts[0], freq))
	words.sort(key = lambda x: x[1], reverse = True)
	return (words, total)

(words, total) = readwords('words')

def score(guess, hidden):
	wordlength = len(guess)
	ret = 0
	unchecked = []
	# Calculate all the greens first. If the hidden word is LIMBO and the guess is PHONO,
	# you don't get a yellow box for the first O.
	for i in range(wordlength):
		if guess[i] == hidden[i]:
			ret |= 2 << ((wordlength - 1 - i) * 4)
		else:
			unchecked.append(i)
	index = [0] * 127
	for i in unchecked:
		index[ord(hidden[i])] += 1
	for i in unchecked:
		g = ord(guess[i])
		if index[g] > 0:
			ret |= 1 << ((wordlength - 1 - i) * 4)
			index[g] -= 1
	return ret

def test():
	def eq(hidden, guess, expected):
		actual = score(guess, hidden)
		if actual != expected:
			print("h={} g={}, actual={:05x}, expected={:05x}".format(hidden, guess, actual, expected))

	eq("limbo", "phono", 0x00002)
	eq("limbo", "hello", 0x00102)
	eq("hello", "hello", 0x22222)
	eq("tares", "stare", 0x11111)
	eq("limbo", "could", 0x01010)
	eq("hello", "could", 0x01020)
	eq("could", "hello", 0x00021)
	eq("colds", "llama", 0x10000)
	eq("abroad", "action", 0x200010)
	eq("absolute", "disposal", 0x00201011)
	eq("2+4*5=22", "9*3-1=26", 0x01000220)

def profile():
	for w in words:
		for h in words[:1000]:
			score(w, h)

def readscore(wordlength):
	while (True):
		print("Enter score using -gy: ", end='')
		s = input()
		if len(s) != wordlength:
			print("input not {} characters".format(wordlength))
			continue
		if len(re.findall("[-gy]", s)) != wordlength:
			print("invalid input character")
			continue
		ret = 0
		for i in range(wordlength):
			ret *= 16
			if s[i] == 'g':
				ret += 2
			elif s[i] == 'y':
				ret += 1
		return ret

def writescore(score, guess):
	print("\033[37m\033[1m", end='')
	for i in range(5):
		c = guess[i].upper()
		offset = 16 - 4 * i
		b = (score >> offset) & 3
		if b == 0:
			bgcolor = 40
		elif b == 1:
			bgcolor = 43
		elif b == 2:
			bgcolor = 42
		print("\033[{}m{}".format(bgcolor, c), end='')
	print("\033[0m")

def choose(candidates, hard=False):
	if len(candidates) == 1:
		return candidates[0][0]
	best_guess = (0, False, 0, "")
	for w, f in (candidates if hard else words):
		scores = defaultdict(int)
		for h, freq in candidates:
			scores[score(w, h)] += freq

		ps = [ scores[h] / total for h in scores ]
		entropy = -sum([ p * math.log(p) / math.log(2) for p in ps ])
		# Sort by entropy.
		# All else equal choose a candidate word instead of one from the corpus.
		# All else equal choose a more common word.
		guess = (entropy, (w, f) in candidates, f, w)
		if guess > best_guess:
			best_guess = guess
	return best_guess[3]

def top(candidates):
	guesses = []
	for w, _ in words:
		scores = defaultdict(int)
		for h, _ in candidates:
			scores[score(w, h)] += 1

		ps = [ scores[h]/len(words) for h in scores ]
		entropy = -sum([ p * math.log(p) / math.log(2) for p in ps ])
		m = max([ scores[h] for h in scores ])

		guesses.append((entropy, len(scores), m, w))
	for (e, b, m, w) in sorted(guesses, reverse=True):
		print("{:.4f}".format(e), b, m, w)

def play(mode, hard, hidden, guesses):
	candidates = words
	wordlength = len(words[0][0])
	end = 0
	for i in range(wordlength):
		end = (end << 4) + 2
	for i in range(6):
		if len(candidates) >= 10:
			print("Remaining:", len(candidates))
		else:
			print("Remaining:", len(candidates), candidates)
		guess = choose(candidates, hard) if i >= len(guesses) else guesses[i]
		if mode == Mode.play:
			pattern = score(guess, hidden)
			print("Guess {}: ".format(i+1), end='')
			writescore(pattern, guess)
		elif mode == Mode.adversary:
			pattern = worst(candidates, guess)
			print("Guess {}: ".format(i+1), end='')
			writescore(pattern, guess)
		elif mode == Mode.interactive:
			print("Guess {}:".format(i+1), guess)
			pattern = readscore(wordlength)
		if pattern == end:
			break
		candidates = [ (w, f) for w, f in candidates if score(guess, w) == pattern ]


def worst(candidates, guess):
	scores = defaultdict(int)
	for h, f in candidates:
		scores[score(guess, h)] += -math.log(f/total)

	return max([(scores[p], p) for p in scores])[1]

def search(guesses, candidates, depth=1):
	if len(candidates) == 1:
		return 0
	if depth == 6:
		print(candidates)
		return len(candidates) - 1
	guess = choose(candidates) if depth > len(guesses) else guesses[depth-1]
	scores = defaultdict(list)
	for h, f in candidates:
		scores[score(guess, h)].append((h, f))
	i = 0
	unreachable = 0
	for s in scores:
		unreachable += search(guesses, scores[s], depth+1)
		if depth == 1:
			i += 1
			print("{}/{}".format(i, len(scores)))
	return unreachable


def expected(guesses, candidates, depth=1):
	if len(candidates) == 1:
		return depth * candidates[0][1] / total
	guess = choose(candidates) if depth > len(guesses) else guesses[depth-1]
	scores = defaultdict(list)
	for h, f in candidates:
		scores[score(guess, h)].append((h, f))
	i = 0
	e = 0
	for s in scores:
		e += expected(guesses, scores[s], depth+1)
		if depth == 1:
			i += 1
			print("{}/{}".format(i, len(scores)))
	return e

if len(sys.argv) == 1:
	play(Mode.interactive, False, "", sys.argv[1:])
elif sys.argv[1] == "play":
	play(Mode.play, False, sys.argv[2], sys.argv[3:])
elif sys.argv[1] == "hard":
	play(Mode.play, True, sys.argv[2], sys.argv[3:])
elif sys.argv[1] == "adversary":
	play(Mode.adversary, False, "", sys.argv[2:])
elif sys.argv[1] == "search":
	print(search(sys.argv[2:], words))
elif sys.argv[1] == "top":
	top(words)
elif sys.argv[1] == "score":
	print("{0:b}".format(score(sys.argv[3], sys.argv[2])))
elif sys.argv[1] == "profile":
	profile()
elif sys.argv[1] == "test":
	test()
elif sys.argv[1] == "exp":
	print(expected(sys.argv[2:], words))
else:
	play(Mode.interactive, False, "", sys.argv[1:])
