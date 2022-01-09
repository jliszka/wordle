package main

import (
    "bufio"
    "fmt"
    "log"
    "os"
    "strings"
    "strconv"
    "math"
)

type Word struct {
    word string
    freq float64
    n int
}

var words []Word
var total float64
var count float64

func score(guess string, hidden string) int {
    var ret int
    var checked [5]bool
    for i := 0; i < 5; i++ {
        if guess[i] == hidden[i] {
            ret |= 2 << ((4 - i) * 4)
            checked[i] = true
        }
    }
    var index [26]int
    for i := 0; i < 5; i++ {
        if !checked[i] {
            index[int(hidden[i] - 'a')] += 1
        }
    }
    for i := 0; i < 5; i++ {
        if !checked[i] {
            g := int(guess[i] - 'a')
            if index[g] > 0 {
                ret |= 1 << ((4 - i) * 4)
                index[g] -= 1
            }
        }
    }
    return ret
}

type Guess struct {
    word string
    entropy float64
    candidate bool
    freq float64
}

func (g Guess) betterThan(g2 Guess) bool {
    if g.entropy > g2.entropy {
        return true
    }
    if g.entropy < g2.entropy {
        return false
    }
    if g.candidate && !g2.candidate {
        return true
    }
    if !g.candidate && g2.candidate {
        return false
    }
    return g.freq > g2.freq
}

func choose(candidates []Word, hard bool) string {
    if len(candidates) == 1 {
        return candidates[0].word
    }
    choices := words
    if hard {
        choices = candidates
    }

    guesses := make(chan Guess)
    for i, w := range choices {
        go func(i int, w Word) {
            scores := map[int]float64{}
            is_candidate := false
            for _, h := range candidates {
                s := score(w.word, h.word)
                scores[s] += h.freq
                if !hard && w.n == h.n {
                    is_candidate = true
                }
            }
            entropy := 0.0
            for _, fq := range scores {
                pr := fq / total
                entropy -= pr * math.Log2(pr)
            }
            guesses <- Guess{w.word, entropy, is_candidate, w.freq}
        }(i, w)
    }

    best_guess := Guess{"", 0.0, false, 0}
    for range choices {
        guess := <-guesses
        if guess.betterThan(best_guess) {
            best_guess = guess
        }
    }
    return best_guess.word
}

func writescore(score int, guess string) {
    fmt.Printf("\033[37m\033[1m")
    for i := 0; i < 5; i++ {
        c := guess[i] - 'a' + 'A'
        offset := 16 - 4 * i
        b := (score >> offset) & 3
        var bgcolor int
        switch b {
        case 0:
            bgcolor = 40
        case 1:
            bgcolor = 43
        case 2:
            bgcolor = 42
        }
        fmt.Printf("\033[%dm%c", bgcolor, c)
    }
    fmt.Printf("\033[0m\n")
}

func play(hard bool, hidden string) {
    candidates := words
    for i := 0; i < 6; i++ {
        fmt.Printf("Remaining: %d\n", len(candidates))
        guess := choose(candidates, hard)
        pattern := score(guess, hidden)
        fmt.Printf("Guess %d: ", i+1)
        writescore(pattern, guess)
        if pattern == 0x22222 {
            break
        }
        var next_candidates []Word
        for _, c := range candidates {
            if score(guess, c.word) == pattern {
                next_candidates = append(next_candidates, c)
            }
        }
        candidates = next_candidates
    }
}

func expected(candidates []Word, depth int) float64 {
    if len(candidates) == 1 {
        return float64(depth) * candidates[0].freq / total
    }

    guess := choose(candidates, false)
    scores := map[int][]Word{}
    for _, h := range candidates {
        s := score(guess, h.word)
        scores[s] = append(scores[s], h)
    }
    i := 0
    e := 0.0
    for _, cs := range scores {
        e += expected(cs, depth+1)
        if depth == 1 {
            i += 1
            fmt.Printf("\r%d/%d",  i, len(scores))
        }
    }
    return e
}

func failure(candidates []Word, depth int) float64 {
    if len(candidates) == 1 {
        return 0.0
    }
    if depth == 6 {
        ret := 0.0
        for _, c := range candidates {
            ret += c.freq / total
        }
        return ret
    }

    guess := choose(candidates, false)
    scores := map[int][]Word{}
    for _, h := range candidates {
        s := score(guess, h.word)
        scores[s] = append(scores[s], h)
    }
    i := 0
    e := 0.0
    for _, cs := range scores {
        e += failure(cs, depth+1)
        if depth == 1 {
            i += 1
            fmt.Printf("\r%d/%d",  i, len(scores))
        }
    }
    return e
}

func eq(hidden string, guess string, expected int) {
    actual := score(guess, hidden)
    if actual != expected {
        fmt.Printf("h=%s g=%s actual=%05x expected=%05x\n", hidden, guess, actual, expected)
    }
}

func test() {
    eq("limbo", "phono", 0x00002)
    eq("limbo", "hello", 0x00102)
    eq("hello", "hello", 0x22222)
    eq("tares", "stare", 0x11111)
    eq("limbo", "could", 0x01010)
    eq("hello", "could", 0x01020)
    eq("could", "hello", 0x00021)
    eq("colds", "llama", 0x10000)    
}

func main() {
    file, err := os.Open("words")
    if err != nil {
        log.Fatalf("readLines: %s", err)
    }
    defer file.Close()

    words = make([]Word, 12972)
    i := 0
    scanner := bufio.NewScanner(file)
    for scanner.Scan() {
        line := scanner.Text()
        parts := strings.Fields(line)
        freq, err := strconv.Atoi(parts[1])
        if err == nil {
            words[i] = Word{parts[0], float64(freq), i}
            total += float64(freq)
            i++
        }
    }
    count = float64(i)

    test()

    switch os.Args[1] {
    case "play":
        play(false, os.Args[2])
    case "hard":
        play(true, os.Args[2])
    case "exp":
        fmt.Printf("\n%f\n", expected(words, 1))
    case "fail":
        fmt.Printf("\n%f\n", failure(words, 1))
    }    
}
