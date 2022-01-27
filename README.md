# wordle

A [wordle](https://www.powerlanguage.co.uk/wordle/) solver. The default strategy chooses the word with the highest information entropy, but other strategies are supported as well. Probabilities are calculated using English word usage frequencies taken from [Wikipedia](https://en.wiktionary.org/wiki/Wiktionary:Frequency_lists/PG/2006/04/1-10000). The universe of potential words is the 12,972 words accepted by wordle as valid words, not the smaller set of ~2,500 actual solutions.

Each guess groups the remaining candidate words into buckets according to what pattern of colors you would get if that was the hidden word. The general idea is to choose the word that is most likely to put you into a bucket with a small number of words in it.

One way to do that is to choose the word that gives the smallest expected bucket size.

<img src="https://render.githubusercontent.com/render/math?math=S(g) = \sum_{b \in B(g)} \|b\|P(b)">

`B(g)` is the set of buckets produced by guess `g`. `P(b)` is the probability that a word is in the given bucket given English word frequencies.

Another way is to choose the word with the highest information entropy, which penalizes large buckets more, and indicates the number of bits of information you would get by guessing that word.

<img src="https://render.githubusercontent.com/render/math?math=S(g) = -\sum_{b \in B(g)} P(b)\log{P(b)}">

Both approaches work almost equally well, solving in an expected 3.87 guesses and solving in under 3 guesses 25.5% of the time.

See [this twitter thread](https://twitter.com/jliszka/status/1478850816182304769?s=20) for discussion.

```
$ time go run wordle.go solve spore
Remaining: 12972
Guess 1: TARES
Remaining: 47
Guess 2: PHONE
Remaining: 1
Guess 3: SPORE

real	0m0.918s
user	0m8.246s
sys	0m0.546s
```

## Usage

Solver
```
wordle [-h] [-d] [-m exp|num|max] solve <hidden word> [guess1 [guess2 ...]]
   -h hard mode
   -d debug mode (show remaining words when candidate set is small)
   -m choose strategy:
        default: maximize information entropy
        exp: minimize expected bucket size
        num: maximize number of buckets
        max: minimize the size of the largest bucket
   guess1 ...   optional forced initial guesses
```

Interactive mode. Solves wordle for you by telling you what to guess. Not recommended if you like fun.
```
wordle [-h] [-d] [-m exp|num|max] play [guess1 [guess2 ...]]


$ ./wordle -d play
Remaining: 12972
Guess 1: TARES
Enter score using -gy: -yy-y
Remaining: 41
Guess 2: SCALP
Enter score using -gy: g-yy-
Remaining: 1 [solar]
Guess 3: SOLAR
Enter score using -gy: ggggg
```

Calculate the number of expected guesses for the given strategy and initial guesses
```
wordle [-h] [-m exp|num|max] exp [guess1 [guess2 ...]]
```

Calculate the chance of not getting it in 3 tries (aka failure) for the given strategy
```
wordle [-h] [-m exp|num|max] fail
```


## Python version
Much slower but has a couple of additional features.

To solve
```
wordle.py play <hidden word> [guess1 [guess2 ...]]
```


For hard mode
```
wordle.py hard <hidden word> [guess1 [guess2 ...]]
```

To have the computer pick a word adversarially:
```
wordle.py adversary [guess1 [guess2 ...]]
```

To search the entire tree (easy mode) for words below depth 6:
```
wordle.py search
```

To display all words sorted by information entropy as an initial guess:
```
wordle.py top
```

To play interactively
```
wordle.py [guess1 [guess2 ...]]
```
