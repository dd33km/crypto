# -*- coding: utf-8 -*-
"""Strictly educational bit-oriented Feistel network used by the GUI."""
from __future__ import annotations
from typing import Dict, List, Tuple
from .sbox import generate_sbox, substitute_bytes

SUPPORTED_BLOCK_BITS = (16, 32, 64, 128, 256)


def clean_binary(value: str) -> str:
    value = "".join(value.split())
    if not value:
        raise ValueError("Введите двоичное значение")
    if any(ch not in "01" for ch in value):
        raise ValueError("Разрешены только символы 0 и 1")
    return value


def choose_block_size(bit_length: int) -> int:
    for size in SUPPORTED_BLOCK_BITS:
        if bit_length <= size:
            return size
    # keep even and byte aligned for S-box processing
    return ((bit_length + 15) // 16) * 16


def pad_both_sides(bits: str, target: int) -> Tuple[str, Dict[str, int | str]]:
    if len(bits) > target:
        raise ValueError(f"Значение длиннее требуемых {target} бит")
    missing = target - len(bits)
    left = (missing + 1) // 2
    right = missing - left
    padded = "0" * left + bits + "0" * right
    return padded, {"before": bits, "after": padded, "left": left, "right": right, "target": target}


def xor_bits(a: str, b: str) -> str:
    if len(a) != len(b):
        raise ValueError("Для XOR длины должны совпадать")
    return "".join("1" if x != y else "0" for x, y in zip(a, b))


def rotate_right(bits: str, count: int = 1) -> str:
    if not bits:
        return bits
    count %= len(bits)
    return bits[-count:] + bits[:-count] if count else bits


def rotate_left(bits: str, count: int = 1) -> str:
    if not bits:
        return bits
    count %= len(bits)
    return bits[count:] + bits[:count] if count else bits


def bits_to_hex(bits: str) -> str:
    width = max(1, (len(bits) + 3) // 4)
    return f"{int(bits or '0', 2):0{width}X}"


def make_round_keys(base_key: str, rounds: int) -> List[str]:
    """Transparent educational schedule: rotate the padded key left each round."""
    return [rotate_left(base_key, i) for i in range(rounds)]


def F(block: str, key: str, sbox: List[int] | None = None) -> Dict[str, object]:
    """Exactly: Block XOR Key -> S-box -> RotateRight(1 bit)."""
    if len(block) != len(key):
        target = max(len(block), len(key))
        target = ((target + 7) // 8) * 8
        block, block_pad = pad_both_sides(block, target)
        key, key_pad = pad_both_sides(key, target)
    else:
        block_pad = {"before": block, "after": block, "left": 0, "right": 0, "target": len(block)}
        key_pad = {"before": key, "after": key, "left": 0, "right": 0, "target": len(key)}
    xored = xor_bits(block, key)
    sbox_out, lookups = substitute_bytes(xored, sbox or generate_sbox())
    rotated = rotate_right(sbox_out, 1)
    return {
        "block": block, "key": key, "block_padding": block_pad, "key_padding": key_pad,
        "xor": xored, "sbox": sbox_out, "sbox_lookups": lookups, "rotated": rotated, "result": rotated,
    }


def _enrich(round_no: int, L: str, R: str, key: str, fdata: Dict[str, object], new_L: str, new_R: str) -> Dict[str, object]:
    """Trace for the left-oriented educational Feistel round.

    The UI intentionally starts from the LEFT half, matching the visual scheme:
        F(L, K) = RotateRight(S-box(L XOR K), 1)
        L(i+1) = R(i) XOR F(L(i), K(i))
        R(i+1) = L(i)
    """
    return {
        "round": round_no,
        "L_in": L,
        "R_in": R,
        "K": key,
        "function_input": "L",
        "xor_lk": fdata["xor"],
        # legacy alias kept so older integrations do not crash
        "xor_rk": fdata["xor"],
        "sbox_out": fdata["sbox"],
        "sbox_lookups": fdata["sbox_lookups"],
        "F_out": fdata["result"],
        "xor_rf": new_L,
        # legacy alias kept for previous UI/tests
        "xor_lf": new_L,
        "L_out": new_L,
        "R_out": new_R,
    }


def encrypt(block_bits: str, key_bits: str, rounds: int, sbox: List[int] | None = None):
    raw_block = clean_binary(block_bits)
    raw_key = clean_binary(key_bits)
    block_size = choose_block_size(max(len(raw_block), len(raw_key) * 2))
    if block_size % 16:
        block_size += 16 - block_size % 16
    half = block_size // 2
    padded_block, block_padding = pad_both_sides(raw_block, block_size)
    padded_key, key_padding = pad_both_sides(raw_key, half)
    keys = make_round_keys(padded_key, rounds)
    sbox = sbox or generate_sbox()
    L, R = padded_block[:half], padded_block[half:]
    trace = []
    for i, rk in enumerate(keys, start=1):
        # User-requested orientation: all F operations start from LEFT block.
        fdata = F(L, rk, sbox)
        new_L = xor_bits(R, fdata["result"])
        new_R = L
        trace.append(_enrich(i, L, R, rk, fdata, new_L, new_R))
        L, R = new_L, new_R
    return {
        "operation": "encrypt", "input": raw_block, "key_input": raw_key,
        "block_size": block_size, "half_size": half,
        "block_padding": block_padding, "key_padding": key_padding,
        "round_keys": keys, "rounds": trace, "result": L + R,
    }


def decrypt(block_bits: str, key_bits: str, rounds: int, sbox: List[int] | None = None):
    raw_block = clean_binary(block_bits)
    raw_key = clean_binary(key_bits)
    block_size = choose_block_size(max(len(raw_block), len(raw_key) * 2))
    if block_size % 16:
        block_size += 16 - block_size % 16
    half = block_size // 2
    padded_block, block_padding = pad_both_sides(raw_block, block_size)
    padded_key, key_padding = pad_both_sides(raw_key, half)
    keys = make_round_keys(padded_key, rounds)
    sbox = sbox or generate_sbox()
    L, R = padded_block[:half], padded_block[half:]
    trace = []
    # Inverse of: L' = R XOR F(L,K), R' = L
    for display_idx, rk in enumerate(reversed(keys), start=1):
        source_round = rounds - display_idx + 1
        prev_L = R
        fdata = F(prev_L, rk, sbox)
        prev_R = xor_bits(L, fdata["result"])
        step = _enrich(source_round, prev_L, prev_R, rk, fdata, L, R)
        step["decrypt_view"] = True
        trace.append(step)
        L, R = prev_L, prev_R
    return {
        "operation": "decrypt", "input": raw_block, "key_input": raw_key,
        "block_size": block_size, "half_size": half,
        "block_padding": block_padding, "key_padding": key_padding,
        "round_keys": keys, "rounds": trace, "result": L + R,
    }


# ---------------------------------------------------------------------------
# Self-contained educational Feistel container used by the Feistel GUI.
# It intentionally stores the key together with the ciphertext so a student
# can copy one value to the "Расшифровка" tab and reproduce the operation
# without re-entering parameters. This is for visualization/teaching only.
# ---------------------------------------------------------------------------
def build_teaching_container(*, ciphertext_binary: str, key_binary: str, rounds: int,
                             input_mode: str, original_bit_length: int,
                             padding_left: int, padding_right: int,
                             sbox: List[int]) -> str:
    import base64
    import json

    payload = {
        "format_version": 2,
        "algorithm": "Feistel-Teaching",
        "ciphertext_binary": clean_binary(ciphertext_binary),
        "key_binary": clean_binary(key_binary),
        "rounds": int(rounds),
        "input_mode": input_mode if input_mode in ("text", "binary") else "binary",
        "original_bit_length": int(original_bit_length),
        "padding_left": int(padding_left),
        "padding_right": int(padding_right),
        "sbox": [int(v) & 0xFF for v in sbox],
    }
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii")


def parse_teaching_container(container_str: str) -> Dict[str, object]:
    import base64
    import json

    value = "".join(container_str.split())
    if not value:
        raise ValueError("Вставьте контейнер шифротекста")
    try:
        raw = base64.urlsafe_b64decode(value.encode("ascii"))
        payload = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise ValueError("Это не контейнер Feistel, полученный на вкладке «Шифровка»") from exc

    if payload.get("algorithm") != "Feistel-Teaching":
        raise ValueError("Контейнер относится не к учебной сети Фейстеля")
    required = (
        "ciphertext_binary", "key_binary", "rounds", "original_bit_length",
        "padding_left", "padding_right", "sbox"
    )
    if any(k not in payload for k in required):
        raise ValueError("В контейнере Feistel не хватает параметров")

    payload["ciphertext_binary"] = clean_binary(str(payload["ciphertext_binary"]))
    payload["key_binary"] = clean_binary(str(payload["key_binary"]))
    payload["rounds"] = int(payload["rounds"])
    payload["original_bit_length"] = int(payload["original_bit_length"])
    payload["padding_left"] = int(payload["padding_left"])
    payload["padding_right"] = int(payload["padding_right"])
    sbox = payload["sbox"]
    if not isinstance(sbox, list) or len(sbox) != 256:
        raise ValueError("Некорректная S-box в контейнере Feistel")
    payload["sbox"] = [int(v) & 0xFF for v in sbox]
    return payload


def remove_original_padding(padded_bits: str, *, original_bit_length: int, padding_left: int) -> str:
    padded_bits = clean_binary(padded_bits)
    start = max(0, int(padding_left))
    end = start + max(0, int(original_bit_length))
    if end > len(padded_bits):
        raise ValueError("Данные контейнера повреждены: неверные параметры padding")
    return padded_bits[start:end]

# ---------------------------------------------------------------------------
# Backward-compatible byte API retained for the original project/tests.
# The GUI above uses the bit-oriented educational API.  These wrappers keep
# existing callers working without changing AES or old integration code.
# ---------------------------------------------------------------------------
import hashlib as _hashlib
import base64 as _base64
import json as _json


def generate_round_keys(key: bytes, num_rounds: int, half_block_bytes: int) -> List[bytes]:
    keys = []
    for i in range(1, num_rounds + 1):
        digest = _hashlib.sha256(key + i.to_bytes(4, "big")).digest()
        keys.append(digest[:half_block_bytes])
    return keys


def _bytes_to_bits(data: bytes) -> str:
    return "".join(f"{b:08b}" for b in data)


def _bits_to_bytes(bits: str) -> bytes:
    return bytes(int(bits[i:i+8], 2) for i in range(0, len(bits), 8))


def _F_bytes(right: bytes, round_key: bytes, sbox=None) -> bytes:
    if len(right) != len(round_key):
        raise ValueError("Длина правой половины и раундового ключа должны совпадать")
    fdata = F(_bytes_to_bits(right), _bytes_to_bits(round_key), sbox or generate_sbox())
    return _bits_to_bytes(fdata["result"])


def feistel_round(L: bytes, R: bytes, round_key: bytes, sbox=None):
    f_output = _F_bytes(R, round_key, sbox)
    new_L = R
    new_R = bytes(a ^ b for a, b in zip(L, f_output))
    return new_L, new_R, {"L_in": L, "R_in": R, "K": round_key, "F_out": f_output, "L_out": new_L, "R_out": new_R}


def feistel_inverse_round(L: bytes, R: bytes, round_key: bytes, sbox=None):
    prev_R = L
    f_output = _F_bytes(prev_R, round_key, sbox)
    prev_L = bytes(a ^ b for a, b in zip(R, f_output))
    return prev_L, prev_R, {"L_in": L, "R_in": R, "K": round_key, "F_out": f_output, "L_out": prev_L, "R_out": prev_R}


def feistel_encrypt_block(block: bytes, round_keys: List[bytes], sbox=None):
    half = len(block) // 2
    L, R = block[:half], block[half:]
    trace = [{"round": 0, "stage": "InitialState", "L": L, "R": R}]
    for i, rk in enumerate(round_keys, 1):
        L, R, step = feistel_round(L, R, rk, sbox)
        step.update(round=i, stage="Round")
        trace.append(step)
    trace.append({"round": len(round_keys), "stage": "Ciphertext", "L": L, "R": R})
    return L + R, trace


def feistel_decrypt_block(block: bytes, round_keys: List[bytes], sbox=None):
    half = len(block) // 2
    L, R = block[:half], block[half:]
    trace = [{"round": len(round_keys), "stage": "InitialState(Ciphertext)", "L": L, "R": R}]
    for i, rk in enumerate(reversed(round_keys), 1):
        rn = len(round_keys) - i + 1
        L, R, step = feistel_inverse_round(L, R, rk, sbox)
        step.update(round=rn, stage="InverseRound")
        trace.append(step)
    trace.append({"round": 0, "stage": "PlaintextBlock", "L": L, "R": R})
    return L + R, trace


def feistel_encrypt(data: bytes, key: bytes, num_rounds: int, block_size_bytes: int = 8, sbox=None):
    if len(data) % block_size_bytes:
        raise ValueError("Длина данных должна быть кратна размеру блока")
    rks = generate_round_keys(key, num_rounds, block_size_bytes // 2)
    blocks, traces = [], []
    for i in range(0, len(data), block_size_bytes):
        out, tr = feistel_encrypt_block(data[i:i+block_size_bytes], rks, sbox)
        blocks.append(out); traces.append(tr)
    return blocks, traces, rks


def feistel_decrypt(ciphertext_blocks: List[bytes], key: bytes, num_rounds: int, block_size_bytes: int = 8, sbox=None):
    rks = generate_round_keys(key, num_rounds, block_size_bytes // 2)
    blocks, traces = [], []
    for block in ciphertext_blocks:
        out, tr = feistel_decrypt_block(block, rks, sbox)
        blocks.append(out); traces.append(tr)
    return blocks, traces


FEISTEL_FORMAT_VERSION = 1

def build_feistel_container(ciphertext_hex: str, original_length_bytes: int, num_rounds: int, block_size_bytes: int) -> str:
    payload = {"format_version": FEISTEL_FORMAT_VERSION, "algorithm": "Feistel", "rounds": num_rounds,
               "block_size_bytes": block_size_bytes, "original_length_bytes": original_length_bytes,
               "ciphertext_hex": ciphertext_hex}
    return _base64.b64encode(_json.dumps(payload, ensure_ascii=False).encode("utf-8")).decode("ascii")


def parse_feistel_container(container_str: str):
    try:
        payload = _json.loads(_base64.b64decode(container_str.strip()).decode("utf-8"))
    except Exception as exc:
        raise ValueError(f"Не удалось разобрать контейнер шифротекста Фейстеля: {exc}") from exc
    required = ["algorithm", "rounds", "block_size_bytes", "original_length_bytes", "ciphertext_hex"]
    if payload.get("algorithm") != "Feistel" or any(k not in payload for k in required):
        raise ValueError("Некорректный контейнер Фейстеля")
    return payload
