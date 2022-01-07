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

words = []
with open('words') as f:
	words = f.readlines()
	words = [ w.rstrip() for w in words ]

total = 0
freqs = defaultdict(int)
with open('freqs') as f:
	lines = f.readlines()
	for line in lines:
		parts = line.rstrip().split(' ')
		freqs[parts[1]] += int(parts[0])
		total += int(parts[0])

def score(guess, hidden):
	ret = 0
	unchecked = []
	# Calculate all the greens first. If the hidden word is LIMBO and the guess is PHONO,
	# you don't get a yellow box for the first O.
	for i in range(5):
		if guess[i] == hidden[i]:
			ret |= 2 << ((4 - i) * 4)
		else:
			unchecked.append(i)
	index = [0] * 26
	for i in unchecked:
		index[ord(hidden[i]) - 97] += 1
	for i in unchecked:
		g = ord(guess[i]) - 97
		if index[g] > 0:
			ret |= 1 << ((4 - i) * 4)
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

def profile():
	for w in words:
		for h in words[:1000]:
			score(w, h)

def readscore():
	while (True):
		print("Enter score using -gy: ", end='')
		s = input()
		if len(s) != 5:
			print("input not 5 characters")
			continue
		if len(re.findall("[-gy]", s)) != 5:
			print("invalid input character")
			continue
		ret = 0
		for i in range(5):
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

def choose(candidates, hard):
	print("Searching...")
	if len(candidates) == 1:
		return candidates[0]
	guesses = []
	for w in (candidates if hard else words):
		scores = defaultdict(int)
		for h in candidates:
			scores[score(w, h)] += freqs.get(h, 1)

		ps = [ scores[h] / total for h in scores ]
		entropy = -sum([ p * math.log(p) / math.log(2) for p in ps ])
		# Sort by entropy.
		# All else equal choose a candidate word instead of one from the corpus.
		# All else equal choose a more common word.
		guesses.append((entropy, w in candidates, freqs.get(w, 1), w))
	return max(guesses)[3]

def top(candidates):
	guesses = []
	for w in words:
		scores = defaultdict(int)
		for h in candidates:
			scores[score(w, h)] += 1

		ps = [ scores[h]/len(words) for h in scores ]
		entropy = -sum([ p * math.log(p) / math.log(2) for p in ps ])
		m = max([ scores[h] for h in scores ])

		guesses.append((entropy, len(scores), m, w))
	for (e, b, m, w) in sorted(guesses, reverse=True):
		print("{:.4f}".format(e), b, m, w)

def play(mode, hard, hidden, guesses):
	candidates = words
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
			pattern = readscore()
		if pattern == 0x22222:
			break
		candidates = [ w for w in candidates if score(guess, w) == pattern ]


def worst(candidates, guess):
	scores = defaultdict(int)
	for h in candidates:
		scores[score(guess, h)] += -math.log(freqs.get(h, 1)/total)

	return max([(scores[p], p) for p in scores])[1]

def search(guesses, candidates, depth=1):
	if len(candidates) == 1:
		return 0
	if depth == 6:
		print(candidates)
		return len(candidates) - 1
	guess = choose(candidates) if depth > len(guesses) else guesses[depth-1]
	scores = defaultdict(list)
	for h in candidates:
		scores[score(guess, h)].append(h)
	i = 0
	unreachable = 0
	for s in scores:
		unreachable += search(guesses, scores[s], depth+1)
		if depth == 1:
			i += 1
			print("{}/{}".format(i, len(scores)))
	return unreachable

if sys.argv[1] == "play":
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
else:
	play(Mode.interactive, False, "", sys.argv[1:])
