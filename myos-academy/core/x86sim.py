"""A tiny 32-bit x86 interpreter for the lesson animations.

It runs the small subset of NASM syntax the lessons use (mov, add, sub, imul, inc, dec, xor, cmp, jumps,
push, pop, call, ret, int 0x80) and records the machine state after every instruction. The animation
shows those recorded frames, so the numbers on screen always match what a real CPU would compute.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

MASK = 0xFFFFFFFF
REGISTERS = ("eax", "ebx", "ecx", "edx", "esi", "edi", "ebp", "esp")
# Smaller views of a 32-bit register: name -> (register, lowest bit, width in bits)
SUBREGISTERS = {
    **{f"{x}x": (f"e{x}x", 0, 16) for x in "abcd"},
    **{f"{x}l": (f"e{x}x", 0, 8) for x in "abcd"},
    **{f"{x}h": (f"e{x}x", 8, 8) for x in "abcd"},
}
STACK_TOP = 0x1000
MAX_STEPS = 500

MEM_RE = re.compile(r"^(?:dword\s+)?\[\s*(\w+)\s*(?:([+-])\s*(\w+)\s*)?\]$", re.I)
JUMPS = {
    "jmp": lambda f: True,
    "je": lambda f: f["ZF"], "jz": lambda f: f["ZF"],
    "jne": lambda f: not f["ZF"], "jnz": lambda f: not f["ZF"],
    "jl": lambda f: f["SF"] != f["OF"],
    "jle": lambda f: f["ZF"] or f["SF"] != f["OF"],
    "jg": lambda f: not f["ZF"] and f["SF"] == f["OF"],
    "jge": lambda f: f["SF"] == f["OF"],
}


class SimError(Exception):
    pass


@dataclass
class Frame:
    line: int | None  # 0-based source line just executed (None for the starting frame)
    registers: dict[str, int]
    flags: dict[str, bool]
    stack: list[tuple[int, int]]  # (address, value) from STACK_TOP-4 down to esp
    changed: set[str] = field(default_factory=set)  # registers/flags/"stack" changed by this step
    note: str = ""


def signed(value: int) -> int:
    value &= MASK
    return value - (1 << 32) if value & 0x80000000 else value


def _parse_int(text: str) -> int:
    text = text.strip().lower()
    try:
        return int(text, 16) if text.startswith("0x") else int(text)
    except ValueError:
        raise SimError(f"bộ mô phỏng không hiểu toán hạng '{text}'") from None


@dataclass
class _Instr:
    line: int
    op: str
    args: list[str]


def _parse(source: str) -> tuple[list[_Instr], dict[str, int]]:
    program: list[_Instr] = []
    labels: dict[str, int] = {}
    scope = ""
    for number, raw in enumerate(source.splitlines()):
        text = raw.split(";", 1)[0].strip()
        if not text:
            continue
        match = re.match(r"^([.\w]+):\s*(.*)$", text)
        if match:
            name = match.group(1)
            if name.startswith("."):
                name = scope + name
            else:
                scope = name
            labels[name] = len(program)
            text = match.group(2).strip()
            if not text:
                continue
        op, _, rest = text.partition(" ")
        op = op.lower()
        if op in ("bits", "section", "global", "extern", "org", "db", "dw", "dd", "times") or "equ" in text.split():
            continue
        args = [a.strip() for a in rest.split(",")] if rest.strip() else []
        args = [scope + a if a.startswith(".") else a for a in args]
        program.append(_Instr(number, op, args))
    return program, labels


class Machine:
    def __init__(self, source: str, initial: dict[str, int] | None = None) -> None:
        self.program, self.labels = _parse(source)
        self.reg = {name: 0 for name in REGISTERS}
        self.reg["esp"] = self.reg["ebp"] = STACK_TOP
        self.reg.update(initial or {})
        self.flags = {"ZF": False, "SF": False, "OF": False, "CF": False}
        self.mem: dict[int, int] = {}
        self.pc = self.labels.get("_start", 0)

    # ---- operands ------------------------------------------------------
    def _address(self, operand: str) -> int | None:
        match = MEM_RE.match(operand)
        if not match:
            return None
        base, sign, offset = match.groups()
        address = self.reg[base.lower()]
        if offset:
            delta = _parse_int(offset)
            address += delta if sign == "+" else -delta
        return address & MASK

    def read(self, operand: str) -> int:
        name = operand.lower()
        if name in self.reg:
            return self.reg[name]
        if name in SUBREGISTERS:
            full, shift, width = SUBREGISTERS[name]
            return (self.reg[full] >> shift) & ((1 << width) - 1)
        address = self._address(operand)
        if address is not None:
            return self.mem.get(address, 0)
        return _parse_int(operand) & MASK

    def write(self, operand: str, value: int) -> None:
        name = operand.lower()
        if name in self.reg:
            self.reg[name] = value & MASK
            return
        if name in SUBREGISTERS:
            full, shift, width = SUBREGISTERS[name]
            field_mask = ((1 << width) - 1) << shift
            self.reg[full] = (self.reg[full] & ~field_mask & MASK) | ((value << shift) & field_mask)
            return
        address = self._address(operand)
        if address is None:
            raise SimError(f"không ghi được vào {operand}")
        self.mem[address] = value & MASK

    def push(self, value: int) -> None:
        self.reg["esp"] = (self.reg["esp"] - 4) & MASK
        self.mem[self.reg["esp"]] = value & MASK

    def pop(self) -> int:
        value = self.mem.get(self.reg["esp"], 0)
        self.reg["esp"] = (self.reg["esp"] + 4) & MASK
        return value

    def _set_flags(self, result: int, a: int, b: int, kind: str) -> None:
        r = result & MASK
        self.flags["ZF"] = r == 0
        self.flags["SF"] = bool(r & 0x80000000)
        sa, sb, sr = signed(a), signed(b), signed(r)
        if kind == "add":
            self.flags["OF"] = (sa >= 0) == (sb >= 0) and (sr >= 0) != (sa >= 0)
            self.flags["CF"] = result > MASK
        elif kind == "sub":
            self.flags["OF"] = (sa >= 0) != (sb >= 0) and (sr >= 0) != (sa >= 0)
            self.flags["CF"] = (a & MASK) < (b & MASK)
        else:
            self.flags["OF"] = self.flags["CF"] = False

    # ---- execution -----------------------------------------------------
    def stack_view(self) -> list[tuple[int, int]]:
        return [(addr, self.mem.get(addr, 0)) for addr in range(STACK_TOP - 4, self.reg["esp"] - 1, -4)]

    def step(self) -> tuple[int, bool]:
        """Execute one instruction; return (source line, still running)."""
        instr = self.program[self.pc]
        op, args = instr.op, instr.args
        self.pc += 1
        if op == "mov":
            self.write(args[0], self.read(args[1]))
        elif op in ("add", "sub", "cmp"):
            a, b = self.read(args[0]), self.read(args[1])
            result = a + b if op == "add" else a - b
            self._set_flags(result, a, b, "add" if op == "add" else "sub")
            if op != "cmp":
                self.write(args[0], result)
        elif op in ("inc", "dec"):
            a = self.read(args[0])
            carry = self.flags["CF"]  # inc/dec leave CF alone
            result = a + 1 if op == "inc" else a - 1
            self._set_flags(result, a, 1, "add" if op == "inc" else "sub")
            self.flags["CF"] = carry
            self.write(args[0], result)
        elif op == "xor":
            result = self.read(args[0]) ^ self.read(args[1])
            self._set_flags(result, 0, 0, "logic")
            self.write(args[0], result)
        elif op == "imul":
            result = signed(self.read(args[0])) * signed(self.read(args[1]))
            self.write(args[0], result)
        elif op in JUMPS:
            if JUMPS[op](self.flags):
                self.pc = self._target(args[0])
        elif op == "push":
            self.push(self.read(args[0]))
        elif op == "pop":
            self.write(args[0], self.pop())
        elif op == "call":
            self.push(0xC0DE0000 + self.pc)  # fake but recognisable return address
            self.pc = self._target(args[0])
        elif op == "ret":
            value = self.pop()
            if value >> 16 != 0xC0DE:
                raise SimError("ret lấy phải một giá trị không phải địa chỉ quay về")
            self.pc = value & 0xFFFF
        elif op == "int":
            return instr.line, False  # system call: the animations end the program here
        elif op in ("cli", "hlt", "nop"):
            return instr.line, op != "hlt"
        else:
            raise SimError(f"bộ mô phỏng chưa hỗ trợ lệnh '{op}'")
        return instr.line, self.pc < len(self.program)

    def _target(self, label: str) -> int:
        if label not in self.labels:
            raise SimError(f"không có nhãn '{label}'")
        return self.labels[label]


def trace(source: str, initial: dict[str, int] | None = None) -> list[Frame]:
    """Run the program and return one frame per executed instruction, plus the starting frame."""
    machine = Machine(source, initial)

    def snapshot(line: int | None, before: Frame | None) -> Frame:
        frame = Frame(line, dict(machine.reg), dict(machine.flags), machine.stack_view())
        if before is not None:
            frame.changed = {r for r in REGISTERS if frame.registers[r] != before.registers[r]}
            frame.changed |= {f for f in frame.flags if frame.flags[f] != before.flags[f]}
            if frame.stack != before.stack:
                frame.changed.add("stack")
        return frame

    frames = [snapshot(None, None)]
    running = bool(machine.program)
    while running:
        if len(frames) > MAX_STEPS:
            raise SimError("chương trình chạy quá lâu (có thể vòng lặp vô hạn)")
        line, running = machine.step()
        frames.append(snapshot(line, frames[-1]))
    return frames
