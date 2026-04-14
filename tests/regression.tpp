suite "core suite":
    test "math equality":
        expect 2 plus 3 to be 5
    test "range assertion":
        let score be 8
        expect score to be between 1 and 10
    test "type assertion":
        let message be "hello"
        expect type of message to be str

suite "function suite":
    test "addition function":
        define function add with a and b:
            give back a plus b
        expect call add with 2 and 3 to be 5

suite "fuzzy suite":
    test "fuzzy assignment":
        x is like 4
        increase x by 6
        expect x to be 10

suite "control flow suite":
    test "repeat increments":
        let total be 0
        repeat 3 times:
            change total to total plus 1
        expect total to be 3

    test "count range sum":
        let total be 0
        count from 1 to 4 as i:
            change total to total plus i
        expect total to be 10

suite "stdlib suite":
    test "math multiply":
        bring in math
        expect call math.multiply with 3 and 4 to be 12
