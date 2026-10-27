"""5단계: 암호문 해독하기 — 공개키 (N, e)와 암호문 하나를 보고, N = p × q로 개인키를 만들어 풀어 보기."""
import asyncio
import html
import random

from pyscript import when

import rsa_math
from dom import comma, el, josa, message, run_async, set_html, set_text, set_value, show, value_of

KEY_SIZES = {
    "2": (11, 97),        # 두 자리 소수 → 2단계처럼 암산 가능
    "3": (101, 997),      # 세 자리 소수 → 3단계처럼 계산기 필요
    "5": (10007, 99991),  # 다섯 자리 소수 → 컴퓨터 필요
}

# 비밀 메시지 예시. '새 비밀 메시지'를 누를 때마다 이 중 하나를 무작위로 뽑는다.
SECRET_MESSAGES = [
    "곱하기는 쉽지만 소인수분해는 어렵다!",
    "축하합니다! 암호 해독 성공",
    "RSA는 1977년에 만들어졌어요",
    "N을 쪼갤 수 있는 사람만 비밀을 읽는다",
    "HTTPS 보안에도 RSA가 쓰여요",
    "비밀번호는 아무에게도 알려주지 마세요",
    "소수는 1과 자기 자신으로만 나누어져요",
    "공개키는 자물쇠, 개인키는 열쇠",
    "RSA는 세 사람 이름의 첫 글자예요",
    "2는 유일한 짝수 소수예요",
    "소수는 끝없이 많아요",
    "소인수분해 결과는 단 한 가지뿐!",
    "전자서명에도 RSA가 쓰여요",
    "큰 양자컴퓨터가 생기면 RSA가 위험해요",
    "φ(N)을 알면 개인키 d를 만들 수 있어요",
    "지금 읽은 이 문장도 RSA로 잠겨 있었어요",
    "동아리 부스에 와 줘서 고마워요!",
    "암호학은 수학으로 비밀을 지키는 학문",
    "소수 p와 q는 절대 공개하면 안 돼요",
    "e는 공개해도 되지만 d는 꼭 숨겨요",
    "1은 소수가 아니에요",
    "RSA-2048은 617자리 수를 써요",
    "인터넷 쇼핑할 때도 RSA가 지켜 줘요",
    "슈퍼컴퓨터도 RSA-2048은 못 풀어요",
    "소인수분해가 쉬워지면 RSA는 끝이에요",
    "p와 q가 클수록 암호가 튼튼해져요",
    "수학 시간에 배운 소수가 암호를 지켜요",
    "이 암호를 푼 당신은 해독 전문가!",
]

TABLE_ROWS = 6  # 해독 과정 표에 보여 줄 글자 수

state = {"n": 0, "e": 0, "p": 0, "q": 0, "cipher": [], "mine": False, "last": None}
bag = []  # 아직 안 뽑은 메시지들 (한 바퀴를 다 돌기 전에는 같은 메시지가 다시 나오지 않게)
typing = {"round": 0}  # 해독한 글자를 하나씩 보여 주는 애니메이션의 차례 번호 (바뀌면 하던 애니메이션은 멈춘다)


def draw_message():
    """준비된 메시지 중 하나를 무작위로 뽑는다. 한 바퀴를 다 돌면 다시 섞는다."""
    if not bag:
        bag.extend(random.sample(SECRET_MESSAGES, len(SECRET_MESSAGES)))
        if len(bag) > 1 and bag[-1] == state["last"]:
            bag.insert(0, bag.pop())  # 방금 본 메시지가 곧바로 다시 나오지 않게
    state["last"] = bag.pop()
    return state["last"]


# ── 화면 그리기 ─────────────────────────────────────────

def render_cipher():
    set_text("s5-cipher", " ".join(map(str, state["cipher"])))
    set_text("s5-cipher-count", f"숫자 {len(state['cipher'])}개")
    show("s5-mine", state["mine"])


def clear_result():
    typing["round"] += 1  # 진행 중인 글자 애니메이션 멈추기
    show("s5-feedback", False)
    show("s5-steps", False)
    show("s5-steps-empty")
    set_text("s5-plain", "")


def new_secret():
    keys = rsa_math.generate_keys(KEY_SIZES[value_of("s5-size")])
    state.update(n=keys["n"], e=keys["e"], p=keys["p"], q=keys["q"], mine=False)
    state["cipher"] = rsa_math.encrypt_text(draw_message(), keys["n"], keys["e"])
    set_text("s5-n", comma(keys["n"]))
    set_text("s5-e", keys["e"])
    set_text("s5-n-again", comma(keys["n"]))
    set_text("s5-pq", f"{comma(keys['p'])}\u00a0×\u00a0{comma(keys['q'])}")  # \u00a0 = 줄바꿈 없는 띄어쓰기: 줄이 바뀌어도 p × q는 한 줄에
    render_cipher()
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
        f"<small>{e} × {comma(d)}{josa(d, '을', '를')} {comma(phi)}{josa(phi, '으로', '로')} 나눈 나머지가 1</small></li>"
        f"<li><b>숫자마다 M = C<sup>d</sup> mod N</b>"
        f"<code>{comma(c0)}<sup>{comma(d)}</sup> mod {comma(n)} = {m0}</code>"
        f"<small>암호문의 앞부분 — 바이트 몇 개가 모여 글자 하나가 돼요</small>"
        f'<table class="byte-table"><thead><tr><th>암호문 C</th><th>복호 M (바이트)</th><th>글자</th></tr></thead>'
        f"<tbody>{char_rows(cipher, plain, text)}</tbody></table></li>"
    )


async def type_out(text):
    typing["round"] += 1
    my_round = typing["round"]
    box = el("s5-plain")
    for k in range(1, len(text) + 1):
        if typing["round"] != my_round:
            return
        box.textContent = text[:k]
        await asyncio.sleep(0.05)


def setup():
    new_secret()


def reset():
    """다음 사람을 위해 키 크기를 처음 것으로 돌리고 새 비밀 메시지를 낸다."""
    set_value("s5-size", "2")
    set_value("s5-msg", "")
    new_secret()


# ── 이벤트 ─────────────────────────────────────────────

@when("change", "#s5-size")
def on_size(event):
    new_secret()


@when("click", "#s5-new")
def on_new(event):
    new_secret()


@when("submit", "#s5-form")
def on_decrypt(event):
    event.preventDefault()
    clear_result()
    p, q, n, e = state["p"], state["q"], state["n"], state["e"]
    phi, d = rsa_math.private_key(p, q, e)
    plain = rsa_math.decrypt_numbers(state["cipher"], n, d)
    text = rsa_math.bytes_to_text(plain)
    set_html("s5-steps", steps_html(p, q, n, e, phi, d, state["cipher"], plain, text))
    show("s5-steps")
    show("s5-steps-empty", False)
    message("s5-feedback", f"개인키 d = {comma(d)}{josa(d, '을', '를')} 만들어 암호문을 풀었어요!", "ok")
    run_async(type_out(text))


@when("submit", "#s5-enc-form")
def on_encrypt(event):
    event.preventDefault()
    text = value_of("s5-msg")
    if not text:
        message("s5-feedback", "암호화할 메시지를 입력해 주세요.", "err")
        return
    state["cipher"] = rsa_math.encrypt_text(text, state["n"], state["e"])
    state["mine"] = True
    set_value("s5-msg", "")
    render_cipher()
    clear_result()
    message("s5-feedback", f"내 메시지를 숫자 {len(state['cipher'])}개로 암호화했어요. '해독하기'를 눌러 풀어 보세요!", "ok")
