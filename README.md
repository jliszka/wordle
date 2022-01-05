# wordle

A wordle solver. Choses the word with the highest information entropy among the remaning candidate words. See [this twitter thread](https://twitter.com/jliszka/status/1478850816182304769?s=20) for discussion.

```
$ ./wordle.py swore tares
Remaining: 12972
Guess 1:  tares
Remaining: 47
Guess 2:  poise
Remaining: 5
Guess 3:  winch
Remaining: 1
Guess 4:  swore
```

The best first word is `tares` but it takes a long time to compute that, so you can spot it that guess on the command line.

General usage is
```
wordle.py <hidden word> [guess1 [guess2 ...]]
```

