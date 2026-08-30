# T++ Example: Temperature Converter

define celsius_to_fahrenheit with c as a number, giving back a number as:
    give back (c times 9 / 5) plus 32

define fahrenheit_to_celsius with f as a number, giving back a number as:
    give back (f minus 32) times 5 / 9

let boiling_c be 100
let boiling_f be call celsius_to_fahrenheit with boiling_c
say "{boiling_c}°C in Fahrenheit is {boiling_f}°F"

let freezing_f be 32
let freezing_c be call fahrenheit_to_celsius with freezing_f
say "{freezing_f}°F in Celsius is {freezing_c}°C"
