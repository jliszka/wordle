# wordle

A wordle solver. The default strategy chooses the word with the highest information entropy among the remaning candidate words.

See [this twitter thread](https://twitter.com/jliszka/status/1478850816182304769?s=20) for discussion.

```
$ ./wordle solve spore
Remaining: 12972
Guess 1: TARES
Remaining: 47
Guess 2: PHONE
Remaining: 1
Guess 3: SPORE
```

General usage is
```
wordle.py solve <hidden word> [guess1 [guess2 ...]]
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
