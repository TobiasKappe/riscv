# A (very) incomplete RISC-V assembler and simulator

This library is meant to simulate a trivial fragment of the (32-bit) RISC-V instruction set, consisting of the following instructions:
* `lw` (load word)
* `sw` (store word)
* `add` (arithmetic add)
* `addi` (add immediate)
* `beq` (branch if equal)
* `bge` (branch if greater or equal)
* `blt` (branch if less than)

There is also a small assembler, capable of parsing simple RISC-V assembly code for these instructions, and turning them into machine code.

This is not meant as a serious project, so documentation is minimal. If you want an example of how to use it, refer to `tests/test_implementation.py`.
