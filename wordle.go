package main

import (
    "bufio"
    "fmt"
    "log"
    "os"
    "strings"
    "strconv"
    "math"
    "flag"
    "runtime/pprof"
)

type Mode int
const (
    Solve Mode = iota
    Play
)

type Word struct {
    word string
    freq int
    pr float64
    n int
}

func (w Word) String() string {
        return fmt.Sprintf("%s(%0.0f)", w.word, w.freq);
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

func score2(guess string, hidden string) int {
    var checked [5]bool
    greens := 0
    for i := 0; i < 5; i++ {
        greens *= 3
        if guess[i] == hidden[i] {
            greens += 2
            checked[i] = true
        }
    }
    var index [26]int
    for i := 0; i < 5; i++ {
        if !checked[i] {
            index[int(hidden[i] - 'a')] += 1
        }
    }
    yellows := 0
    for i := 0; i < 5; i++ {
        yellows *= 3
        if !checked[i] {
            g := int(guess[i] - 'a')
            if index[g] > 0 {
                yellows += 1
                index[g] -= 1
            }
        }
    }
    return greens + yellows
}

type Guess struct {
    word string
    metric float64
    candidate bool
    freq float64
}

func (g Guess) betterThan(g2 Guess) bool {
    if g.metric > g2.metric {
        return true
    }
    if g.metric < g2.metric {
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

type Guess2 struct {
    word1 string
    word2 string
    metric float64
}

type Metric func ([243]float64, [243]float64) float64
var metric Metric

func entropy(freq [243]float64, size [243]float64) float64 {
    ret := 0.0
    for i := 0; i < 243; i++ {
        fq := freq[i]
        if fq > 0 {
            pr := fq / total
            ret -= pr * math.Log2(pr)
        }
    }
    return ret
}

func expectedBucket(freq [243]float64, size [243]float64) float64 {
    ret := 0.0
    for i, fq := range freq {
        if fq > 0 {
            pr := fq / total
            ret -= pr * size[i]
        }
    }
    return ret
}

func maxBucket(freq [243]float64, size [243]float64) float64 {
    ret := 0.0
    for _, sz := range size {
        if sz > ret {
            ret = sz
        }
    }
    return -ret
}

func numBuckets(freq [243]float64, size [243]float64) float64 {
    ret := 0.0
    for _, sz := range size {
        if sz > 0 {
            ret += 1
        }
    }
    return ret
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
            var freqs [243]float64
            var sizes [243]float64
            is_candidate := false
            for _, h := range candidates {
                s := score2(w.word, h.word)
                freqs[s] += h.pr
                sizes[s] += 1
                if !hard && w.n == h.n {
                    is_candidate = true
                }
            }
            guesses <- Guess{w.word, metric(freqs, sizes), is_candidate, w.pr}
        }(i, w)
    }

    best_guess := Guess{"xxxxx", -1000000.0, false, 0}
    for range choices {
        guess := <-guesses
        if guess.betterThan(best_guess) {
            best_guess = guess
        }
    }
    return best_guess.word
}

func filter(candidates []Word, scoreStrs []string) {
    var scores [243] int
    var guess_count [243] int
    var sc [243] int
    for _, s := range scoreStrs {
        if s == "/" {
            for i, c := range sc {
                if c > scores[i] {
                    scores[i] = c
                }
                sc[i] = 0
            }
        } else {
            k := parseScore(s)
            sc[k] += 1
            guess_count[k] += 1
        }
    }

    none := Word{"xxxxx", 0, 0.0, -1}
    words := make(chan Word)
    for _, h := range candidates {
        go func(h Word) {
            var count [243]int
            f := 0.0
            for _, g := range candidates {
                s := score2(g.word, h.word)
                if scores[s] > 0 {
                    count[s] += 1
                    f += g.pr * float64(guess_count[s])
                }
            }
            all := true
            for i, c := range scores {
                if count[i] < c {
                    all = false
                    break
                }
            }
            if all {
                words <- Word{h.word, 0, f, 0}
            } else {
                words <- none
            }
        }(h)
    }
    for range candidates {
        w := <-words
        if w.n >= 0 {
            fmt.Printf("%0.0f %s\n", w.freq, w.word)
        }
    }
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

func readscore() int {
    for {
        var score string
        fmt.Print("Enter score using -gy: ")
        fmt.Scanf("%s", &score)
        if len(score) != 5 {
            fmt.Println("Must be 5 characters")
            continue
        }
        ret := 0
        for _, c := range score {
            ret *= 16
            if c == 'g' {
                ret += 2
            } else if c == 'y' {
                ret += 1
            }
        }
        return ret
    }
}

func parseScore(score string) int {
    ret := 0
    for _, c := range score {
        ret *= 3
        if c == 'g' {
            ret += 2
        } else if c == 'y' {
            ret += 1
        }
    }
    return ret
}

func play(hard bool, debug bool, mode Mode, hidden string, guesses []string) {
    candidates := words
    for i := 0; i < 6; i++ {
        if len(candidates) < 20 && debug {
            fmt.Printf("Remaining: %d %s\n", len(candidates), candidates)
        } else {
            fmt.Printf("Remaining: %d\n", len(candidates))
        }

        var guess string
        if i < len(guesses) {
            guess = guesses[i]
        } else {
            guess = choose(candidates, hard)
        }

        var pattern int
        switch mode {
        case Play:
            fmt.Printf("Guess %d: %s\n", i+1, strings.ToUpper(guess))
            pattern = readscore()
        case Solve:
            pattern = score(guess, hidden)
            fmt.Printf("Guess %d: ", i+1)
            writescore(pattern, guess)
        }

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

func top(candidates []Word) Guess2 {
    guesses := make(chan Guess2)
    for _, w1 := range candidates {
        go func(w1 Word) {
            buckets := [243][]Word{}
            for _, h := range candidates {
                s := score2(w1.word, h.word)
                buckets[s] = append(buckets[s], h)
            }
            for _, w2 := range candidates {
                if w1.n <= w2.n {
                    continue
                }
                score := 0.0
                for _, b := range buckets {
                    var freqs [243]float64
                    var sizes [243]float64
                    for _, h := range b {
                        s := score2(w2.word, h.word)
                        freqs[s] += h.pr
                        sizes[s] += 1
                    }
                    score += metric(freqs, sizes)
                }
                guesses <- Guess2{w1.word, w2.word, score}
            }
        }(w1)
    }
    best_guess := Guess2{"xxxxx", "yyyyy", -1000000.0}
    count := len(candidates) * (len(candidates) - 1) / 2
    for i := 0; i < count; i++ {
        if i % 1024 == 0 {
            fmt.Printf("\r%d/%d", i, count)
        }
        guess := <-guesses
        if guess.metric > best_guess.metric {
            best_guess = guess
            fmt.Printf("\n%s/%s\n", guess.word1, guess.word2)
        }
    }
    return best_guess
}

func eval(candidates []Word, guesses []string) float64 {
    if len(guesses) == 1 {
        var freqs [243]float64
        var sizes [243]float64
        for _, h := range candidates {
            s := score2(guesses[0], h.word)
            freqs[s] += h.pr
            sizes[s] += 1
        }
        return metric(freqs, sizes)
    }
    buckets := [243][]Word{}
    for _, h := range candidates {
        s := score2(guesses[0], h.word)
        buckets[s] = append(buckets[s], h)
    }
    score := 0.0
    for _, b := range buckets {
        score += eval(b, guesses[1:])
    }
    return score
}

func expected(hard bool, candidates []Word, depth int, guesses []string) float64 {
    if len(candidates) == 1 {
        return float64(depth) * candidates[0].pr / total
    }

    var guess string
    if depth <= len(guesses) {
        guess = guesses[depth-1]
    } else {
        guess = choose(candidates, hard)
    }
    scores := map[int][]Word{}
    for _, h := range candidates {
        s := score(guess, h.word)
        scores[s] = append(scores[s], h)
    }
    i := 0
    e := 0.0
    for _, cs := range scores {
        e += expected(hard, cs, depth+1, guesses)
        if depth == 1 {
            i += 1
            fmt.Printf("\r%d/%d",  i, len(scores))
        }
    }
    return e
}

func failure(hard bool, candidates []Word, depth int) float64 {
    if len(candidates) == 1 {
        return 0.0
    }
    if depth == 3 {
        ret := 0.0
        for _, c := range candidates {
            ret += c.pr / total
        }
        return ret
    }

    guess := choose(candidates, hard)
    scores := map[int][]Word{}
    for _, h := range candidates {
        s := score(guess, h.word)
        scores[s] = append(scores[s], h)
    }
    i := 0
    e := 0.0
    for _, cs := range scores {
        e += failure(hard, cs, depth+1)
        if depth == 1 {
            i += 1
            fmt.Printf("\r%d/%d",  i, len(scores))
        }
    }
    return e
}

func sigmoid(f int, c float64, k float64) float64 {
    return 1.0 / (1 + math.Exp(-(float64(f)-c)/k))
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

var cpuProfile = flag.String("p", "", "write cpu profile to file")
var hardMode = flag.Bool("h", false, "hard mode")
var metricStr = flag.String("m", "entropy", "evaluation metric")
var debugMode = flag.Bool("d", false, "debug mode")

func main() {
    flag.Parse()

    if *cpuProfile != "" {
        f, err := os.Create(*cpuProfile)
        if err != nil {
            log.Fatal(err)
        }
        pprof.StartCPUProfile(f)
        defer pprof.StopCPUProfile()
    }

    file, err := os.Open("words")
    if err != nil {
        log.Fatalf("readLines: %s", err)
    }
    defer file.Close()

    words = make([]Word, 12947)
    i := 0
    scanner := bufio.NewScanner(file)
    for scanner.Scan() {
        line := scanner.Text()
        parts := strings.Fields(line)
        freq, err := strconv.Atoi(parts[1])
        if err == nil {
            pr := sigmoid(freq, 80, 15)
            words[i] = Word{parts[0], freq, pr, i}
            total += pr
            i++
        }
    }
    count = float64(i)

    test()

    switch *metricStr {
    case "exp":
        metric = expectedBucket
    case "max":
        metric = maxBucket
    case "num":
        metric = numBuckets
    default:
        metric = entropy
    }

    switch flag.Arg(0) {
    case "solve":
        play(*hardMode, *debugMode, Solve, flag.Arg(1), flag.Args()[2:])
    case "play":
        play(*hardMode, *debugMode, Play, "xxxxx", flag.Args()[1:])
    case "exp":
        fmt.Printf("\n%f\n", expected(*hardMode, words, 1, flag.Args()[1:]))
    case "fail":
        fmt.Printf("\n%f\n", failure(*hardMode, words, 1))
    case "top":
        fmt.Printf("\n%s\n", top(words))
    case "eval":
        fmt.Println(eval(words, flag.Args()[1:]))
    case "filter":
        filter(words, flag.Args()[1:])
    }    
}
