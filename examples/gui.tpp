create window titled "T++ GUI" as app
set window size to 480 by 320 for app

create button "Click Me" as clicker in window app
on button click for clicker:
    say "Hello from T++ GUI"

show window app
