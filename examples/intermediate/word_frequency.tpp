# T++ Example: Word Frequency Counter
use words_in and lowercase and ends_with and strip from "text"

let sentence be "T++ is simple. T++ is natural. T++ is expressive."
let lower_sentence be call lowercase with sentence
let words be call words_in with lower_sentence

let frequencies be a map of
for each w in words:
    let clean_w be w
    let is_period be call ends_with with clean_w and "."
    if is_period:
        let clean_w be call strip with clean_w and "."
    if clean_w in frequencies:
        set the clean_w of frequencies to frequencies[clean_w] + 1
    otherwise:
        set the clean_w of frequencies to 1

say "Word count map: " then frequencies
