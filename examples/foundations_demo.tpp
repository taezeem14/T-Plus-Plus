# T++ Stage A Foundations Demo: Modules, Types, and Error Handling

# 1. User-defined function with typed parameters and defaults
define compute_total with price as a number and tax_rate as a number defaulting to 0.05, giving back a number as:
    give back price plus (price times tax_rate)

let subtotal be 100 as a whole number
let total be call compute_total with subtotal
say "Subtotal: " then subtotal then " -> Total: " then total

# 2. Error handling with Try / Handle / Finally
let status be "initial"
try:
    let risky_div be 10 divided by 0
handle MathTppError as e:
    change status to "handled division by zero error"
finally:
    say "Execution status: " then status
