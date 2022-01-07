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
	used = [False, False, False, False, False]
	for i in range(5):
		g = guess[i]
		ret *= 4
		if g == hidden[i]:
			ret += 2
			used[i] = True
		else:
			for j in range(5):
				if not used[j] and g == hidden[j]:
					used[j] = True					
					ret += 1
					break
	return ret

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
		for c in s:
			ret *= 4
			if (c == 'g'):
				ret += 2
			elif (c == 'y'):
				ret += 1
		return ret

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
		print("Guess {}:".format(i+1), guess)
		if mode == Mode.play:
			pattern = score(guess, hidden)
		elif mode == Mode.adversary:
			pattern = worst(candidates, guess)
		elif mode == Mode.interactive:
			pattern = readscore()
		if pattern == 0x2aa:
			break
		candidates = [ w for w in candidates if score(guess, w) == pattern ]


def worst(candidates, guess):
	scores = defaultdict(int)
	for h in candidates:
		scores[score(guess, h)] += -math.log(freqs.get(h, 1)/total)

	return max([(scores[p], p) for p in scores])[1]

def search(candidates, depth=1):
	if len(candidates) == 1:
		return
	if depth == 6:
		print(candidates)
		return
	guess = choose(candidates) if depth > 1 else 'tares' # shortcut
	scores = defaultdict(list)
	for h in candidates:
		scores[score(guess, h)].append(h)
	i = 0
	for s in scores:
		search(scores[s], depth+1)
		if depth == 1:
			i += 1
			print("{}/{}".format(i, len(scores)))

if sys.argv[1] == "play":
	play(Mode.play, False, sys.argv[2], sys.argv[3:])
elif sys.argv[1] == "hard":
	play(Mode.play, True, sys.argv[2], sys.argv[3:])
elif sys.argv[1] == "adversary":
	play(Mode.adversary, False, "", sys.argv[2:])
elif sys.argv[1] == "search":
	search(words)
elif sys.argv[1] == "top":
	top(words)
else:
	play(Mode.interactive, False, "", sys.argv[1:])


