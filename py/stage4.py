"""4단계: 암호문 해독하기 — 공개키 (N, e)와 암호문 여러 개만 보고, N을 소인수분해해서 모두 풀어 보기."""
import asyncio
import html
import random
import time

from pyscript import when

import rsa_math
from dom import comma, el, message, run_async, set_html, set_text, set_value, show, to_int, value_of

KEY_SIZES = {
    "2": (11, 97),        # 두 자리 소수 → 1단계처럼 암산 가능
    "3": (101, 997),      # 세 자리 소수 → 2단계처럼 계산기 필요
    "5": (10007, 99991),  # 다섯 자리 소수 → 컴퓨터 필요
}

SECRET_MESSAGES = [
    "곱하기는 쉽지만 소인수분해는 어렵다!",
    "축하합니다! 암호 해독 성공",
    "RSA는 1977년에 만들어졌어요",
    "N을 쪼갤 수 있는 사람만 비밀을 읽는다",
    "HTTPS 보안에도 RSA가 쓰여요",
    "비밀번호는 아무에게도 알려주지 마세요",
    "소수는 1과 자기 자신으로만 나누어져요",
    "공개키는 자물쇠, 개인키는 열쇠",
]

CIPHER_COUNT = 3           # 한 번에 보여 줄 암호문 개수
TABLE_ROWS = 6             # 해독 과정 표에 보여 줄 글자 수
COMPUTER_LIMIT = 10 ** 14  # 이보다 큰 N을 컴퓨터로 분해하면 브라우저가 한참 멈춘다

state = {"n": 0, "e": 0, "ciphers": []}  # ciphers: [{"nums": [...], "mine": 직접 만든 암호문인지}]
reveal = {"round": 0}


# ── 화면 그리기 ─────────────────────────────────────────

def render_ciphers():
    rows, plains = [], []
    for i, c in enumerate(state["ciphers"]):
        tag = '<span class="tag tag-secret">직접 만듦</span>' if c["mine"] else ""
        rows.append(
            f'<div class="cipher-item"><div class="cipher-label">암호문 {i + 1} {tag}'
            f'<small>숫자 {len(c["nums"])}개</small></div>'
            f'<div class="cipher-nums">{" ".join(map(str, c["nums"]))}</div></div>'
        )
        plains.append(
            f'<div class="plain-item"><span class="plain-idx">{i + 1}</span>'
            f'<div id="s4-plain-{i}" class="plaintext"></div></div>'
        )
    set_html("s4-ciphers", "".join(rows))
    set_html("s4-plains", "".join(plains))


def clear_result():
    reveal["round"] += 1  # 진행 중인 글자 애니메이션 멈추기
    show("s4-feedback", False)
    show("s4-steps", False)
    show("s4-steps-empty")
    for i in range(len(state["ciphers"])):
        set_text(f"s4-plain-{i}", "")


def new_secret():
    keys = rsa_math.generate_keys(KEY_SIZES[value_of("s4-size")])
    state.update(n=keys["n"], e=keys["e"])
    state["ciphers"] = [
        {"nums": rsa_math.encrypt_text(text, keys["n"], keys["e"]), "mine": False}
        for text in random.sample(SECRET_MESSAGES, CIPHER_COUNT)
    ]
    set_text("s4-n", comma(keys["n"]))
    set_text("s4-e", keys["e"])
    render_ciphers()
    set_value("s4-p", "")
    set_value("s4-q", "")
    clear_result()


def char_rows(cipher, plain, text):
    """글자 하나가 바이트 몇 개(=암호문 숫자 몇 개)로 이루어졌는지 묶어서 표의 줄로 만든다."""
    rows, pos = [], 0
    for ch in text[:TABLE_ROWS]:
        size = len(ch.encode("utf-8"))
        cs, ms = cipher[pos:pos + size], plain[pos:pos + size]
        pos += size
        shown = "␣" if ch == " " else html.escape(ch)  # 직접 만든 메시지에 < 같은 글자가 있어도 안전하게
        rows.append(
            f"<tr><td>{' '.join(map(str, cs))}</td><td>{' '.join(map(str, ms))}</td>"
            f'<td class="ch">{shown}</td></tr>'
        )
    return "".join(rows)


def steps_html(p, q, n, e, phi, d, cipher, plain, text):
    c0, m0 = cipher[0], plain[0]
    return (
        f'<li class="inline"><b>p × q = N 확인</b><code>{comma(p)} × {comma(q)} = {comma(n)} ✓</code></li>'
        f'<li class="inline"><b>φ(N) = (p − 1) × (q − 1)</b><code>{comma(p - 1)} × {comma(q - 1)} = {comma(phi)}</code></li>'
        f'<li class="inline"><b>개인키 d = e⁻¹ mod φ(N)</b><code>d = {comma(d)}</code>'
        f"<small>{e} × {comma(d)}을 {comma(phi)}로 나눈 나머지가 1</small></li>"
        f"<li><b>숫자마다 M = C<sup>d</sup> mod N</b>"
        f"<code>{comma(c0)}<sup>{comma(d)}</sup> mod {comma(n)} = {m0}</code>"
        f"<small>암호문 1의 앞부분 — 바이트 몇 개가 모여 글자 하나가 돼요</small>"
        f'<table class="byte-table"><thead><tr><th>암호문 C</th><th>복호 M (바이트)</th><th>글자</th></tr></thead>'
        f"<tbody>{char_rows(cipher, plain, text)}</tbody></table></li>"
    )


async def type_out(texts):
    reveal["round"] += 1
    my_round = reveal["round"]
    for i, text in enumerate(texts):
        box = el(f"s4-plain-{i}")
        for k in range(1, len(text) + 1):
            if reveal["round"] != my_round:
                return
            box.textContent = text[:k]
            await asyncio.sleep(0.04)


def setup():
    new_secret()


# ── 이벤트 ─────────────────────────────────────────────

@when("change", "#s4-size")
def on_size(event):
    new_secret()


@when("click", "#s4-new")
def on_new(event):
    new_secret()


@when("click", "#s4-factor")
def on_factor(event):
    n = state["n"]
    if n > COMPUTER_LIMIT:
        message("s4-feedback", "이 체험에서는 14자리 이하의 N만 컴퓨터로 분해할 수 있어요.", "err")
        return
    t0 = time.perf_counter()
    p = rsa_math.smallest_factor(n)
    spent = time.perf_counter() - t0
    set_value("s4-p", p)
    set_value("s4-q", n // p)
    message("s4-feedback", f"컴퓨터가 {spent:.4f}초 만에 찾았어요: {comma(n)} = {p} × {n // p}", "info")


@when("submit", "#s4-form")
def on_decrypt(event):
    event.preventDefault()
    clear_result()
    n, e = state["n"], state["e"]
    p, q = to_int(value_of("s4-p")), to_int(value_of("s4-q"))

    error = None
    if p is None or q is None:
        error = "N을 소인수분해해서 p와 q를 입력해 주세요."
    elif p * q != n:
        error = f"{comma(p)} × {comma(q)} = {comma(p * q)} → N({comma(n)})과 달라요. 다시 소인수분해해 보세요."
    elif p == q or not (rsa_math.is_prime(p) and rsa_math.is_prime(q)):
        error = "p와 q는 서로 다른 소수여야 해요."
    if error:
        message("s4-feedback", error, "err")
        return

    try:
        phi, d = rsa_math.private_key(p, q, e)
    except ValueError:
        message("s4-feedback", f"e({e})와 φ(N)이 서로소가 아니라서 개인키 d를 만들 수 없어요.", "err")
        return

    plains = [rsa_math.decrypt_numbers(c["nums"], n, d) for c in state["ciphers"]]
    texts = [rsa_math.bytes_to_text(m) for m in plains]
    if any(t is None for t in texts):
        message("s4-feedback", "복호화한 값이 0~255를 벗어났어요. 암호문과 공개키가 짝이 맞는지 확인해 주세요.", "err")
        return
    first = state["ciphers"][0]["nums"]
    set_html("s4-steps", steps_html(p, q, n, e, phi, d, first, plains[0], texts[0]))
    show("s4-steps")
    show("s4-steps-empty", False)
    message("s4-feedback", f"개인키 d = {comma(d)}를 만들어 암호문 {len(texts)}개를 모두 풀었어요!", "ok")
    run_async(type_out(texts))


@when("submit", "#s4-enc-form")
def on_encrypt(event):
    event.preventDefault()
    text = value_of("s4-msg")
    if not text:
        message("s4-feedback", "암호화할 메시지를 입력해 주세요.", "err")
        return
    nums = rsa_math.encrypt_text(text, state["n"], state["e"])
    state["ciphers"] = [{"nums": nums, "mine": True}] + state["ciphers"][: CIPHER_COUNT - 1]
    set_value("s4-msg", "")
    render_ciphers()
    clear_result()
    message("s4-feedback", f"내 메시지를 숫자 {len(nums)}개로 암호화해서 '암호문 1'에 넣었어요. 친구에게 풀어 보게 하세요!", "ok")
