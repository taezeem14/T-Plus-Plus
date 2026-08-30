# T++ Standard Library Documentation

T++ 3.2.0 includes 7 built-in standard library modules.

---

## 1. `math`
Import with: `use ... from "math"`

- `add(a, b)`: Adds two numbers.
- `subtract(a, b)`: Subtracts b from a.
- `multiply(a, b)`: Multiplies two numbers.
- `divide(a, b)`: Divides a by b (raises MathTppError on division by zero).
- `square_root(x)` / `sqrt(x)`: Square root of x.
- `sine(x)` / `sin(x)`: Sine of angle x (radians).
- `cosine(x)` / `cos(x)`: Cosine of angle x (radians).
- `tangent(x)` / `tan(x)`: Tangent of angle x (radians).
- `floor(x)` / `round_down(x)`: Rounds down to nearest whole number.
- `ceil(x)` / `round_up(x)`: Rounds up to nearest whole number.
- `round_number(x, digits=0)`: Rounds to decimal precision.
- `absolute_value(x)` / `abs(x)`: Absolute value.
- `average(numbers)`: Calculates arithmetic mean of a list.
- `median(numbers)`: Calculates median of a list.
- `is_prime(n)`: Checks if integer is prime.
- `is_even(n)` / `is_odd(n)`: Checks parity.
- `random_number(min=0, max=1)`: Generates float in range.
- `random_integer(min, max)`: Generates integer in range.
- Constants: `pi` (3.14159...), `tau` (6.28318...), `e` (2.71828...).

---

## 2. `text`
Import with: `use ... from "text"`

- `uppercase(s)`: Converts string to UPPERCASE.
- `lowercase(s)`: Converts string to lowercase.
- `title(s)`: Converts string to Title Case.
- `capitalized(s)`: Capitalizes first letter.
- `trimmed(s, chars=None)` / `strip(s)`: Strips whitespace or specified characters.
- `padded(s, length, fill=" ")`: Right-justifies string to specified length.
- `replace(s, old, new)`: Replaces occurrences of substring.
- `contains(s, needle)`: Checks if substring exists in text.
- `words_in(s)`: Splits string into list of words.
- `format_currency(amount, symbol="$")`: Formats number as currency string.
- `matches_pattern(s, pattern)`: Evaluates regular expression match.
- `starts_with(s, prefix)` / `ends_with(s, suffix)`: Prefix/suffix checks.

---

## 3. `collections`
Import with: `use ... from "collections"`

- `map_items(fn, items)`: Applies function to each item.
- `filter_items(fn, items)`: Filters items satisfying predicate.
- `reduce_items(fn, items, initial=None)`: Aggregates items with binary function.
- `sort_items(items, reverse=False)`: Returns sorted list.
- `group_by(fn, items)`: Groups items into a map by key selector.
- `unique_items(items)`: Returns list with duplicate items removed.
- `chunk_items(items, size)`: Splits list into sublists of length `size`.
- `flatten(items)`: Flattens one level of nested lists.
- `zip_items(list1, list2)`: Combines two lists pairwise.

---

## 4. `system` (Sandboxed)
Import with: `use ... from "system"`

All filesystem operations are strictly sandboxed within the active workspace root.

- `read_file(path)`: Reads text file contents.
- `write_file(path, content)`: Writes text file.
- `append_file(path, content)`: Appends text to file.
- `file_exists(path)`: Checks if file exists within sandbox.
- `list_files(directory=".")`: Lists filenames in directory within sandbox.
- `get_env(name, default=None)`: Retrieves environment variable.
- `command_line_arguments()`: Returns sys.argv arguments.

---

## 5. `time`
Import with: `use ... from "time"`

- `current_moment()`: Returns current UTC timestamp in ISO 8601 format.
- `format_moment(iso_str, format="%Y-%m-%d %H:%M:%S")`: Formats ISO date string.
- `parse_moment(s, format="%Y-%m-%d %H:%M:%S")`: Parses formatted date into ISO string.
- `time_difference(t1_iso, t2_iso)`: Returns difference between two timestamps in seconds.
- `shift_time(iso_str, days=0, hours=0, minutes=0, seconds=0)`: Adds/subtracts offset.
- `sleep_seconds(seconds)`: Pauses execution (capped by security timeout).
- `millis()`: Epoch time in milliseconds.

---

## 6. `json`
Import with: `use ... from "json"`

- `parse_json(text)`: Parses JSON string into dictionary/list.
- `to_json(data)`: Serializes data structure to JSON string.

---

## 7. `validate`
Import with: `use ... from "validate"`

- `is_valid_email(s)`: Validates email address format.
- `is_valid_number(v)`: Checks if value can be parsed as a float.
- `is_within_range(v, low, high)`: Checks if number is between `low` and `high`.
- `is_not_nothing(v)`: Checks if value is not `None` or `nothing`.
- `is_empty(v)`: Checks if string, list, or map has 0 items.
