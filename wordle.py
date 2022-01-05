#!/usr/bin/env python3

from collections import defaultdict
import math
import sys

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

words = []
with open('words') as f:
	words = f.readlines()
	words = [ w.rstrip() for w in words ]


def choose(candidates):
	if len(candidates) == 1:
		return candidates[0]
	guesses = []
	for w in words: # Easy mode. For hard mode, use `for w in candidates`.
		scores = defaultdict(int)
		for h in candidates:
			scores[score(w, h)] += 1

		ps = [ scores[h]/len(words) for h in scores ]
		entropy = -sum([ p * math.log(p) / math.log(2) for p in ps ])

		guesses.append((entropy, w))
	return max(guesses)[1]

def play(hidden, guesses):
	candidates = words
	for i in range(6):
		print("Remaining: {}".format(len(candidates)))
		guess = choose(candidates) if i >= len(guesses) else guesses[i]
		print("Guess {}: ".format(i+1), guess)
		pattern = score(guess, hidden)
		if pattern == 0x2aa:
			break
		candidates = [ w for w in candidates if score(guess, w) == pattern ]

play(sys.argv[1], sys.argv[2:])

