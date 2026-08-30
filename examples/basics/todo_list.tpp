# T++ Example: Todo List Manager

let tasks be a list containing a record with title as "Buy groceries" and is_done as false, a record with title as "Write documentation" and is_done as true, a record with title as "Review pull requests" and is_done as false

let pending_tasks be the items in tasks where not item's is_done
let done_tasks be the items in tasks where item's is_done

say "Total tasks: " then the length of tasks
say "Pending tasks: " then the length of pending_tasks
say "Completed tasks: " then the length of done_tasks

for each task in pending_tasks:
    say "[ ] " then task's title
