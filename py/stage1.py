"""1단계: 공개키와 개인키 — 숫자 쪼개기(소인수분해)가 어려운 것이 컴퓨터 보안과 무슨 상관인지 알아보기.

공개키 (N, e)는 누구에게나 알려 주고, 개인키 d는 주인만 비밀로 간직한다.
공개키만 보고 개인키를 알아내려면 N을 p × q로 쪼개야 한다.
작은 N은 금방 쪼개져서 개인키가 들통나지만, 실제 RSA의 N은 너무 커서 쪼갤 수 없다.
"""
import asyncio
import math

from pyscript import when

import rsa_examples
import rsa_math
from dom import comma, el, josa, message, run_async, set_state, set_text, show

P, Q = 61, 53                            # 연습용 키를 만드는 두 소수 (시작 화면의 61 × 53 = 3,233과 같다)
REAL_P, REAL_Q = rsa_examples.LEVEL3[0]  # 비교할 실제 RSA-2048 키 (4단계 LEVEL 3의 첫 번째 예시)
MESSAGE = 65                             # 잠갔다가 여는 예시 메시지: 글자 A를 숫자로 바꾼 값 (index.html의 '글자 A'와 같게)
STEP_SECONDS = 0.6                       # 해커가 찾은 값을 한 줄씩 보여 주는 간격(초)

N = P * Q
E = rsa_math.choose_e((P - 1) * (Q - 1))
D = rsa_math.private_key(P, Q, E)[1]
REAL_N = REAL_P * REAL_Q
CELLS = ("s1-pq", "s1-found-d", "s1-real-pq", "s1-real-d")  # 해커가 찾아서 채우는 칸

reveal = {"round": 0}  # 한 줄씩 보여 주는 애니메이션의 차례 번호 (바뀌면 하던 애니메이션은 멈춘다)


def set_cell(cell_id, text, state):
    set_text(cell_id, text)
    set_state(cell_id, state)
    el(cell_id).classList.add("pop")


def clear():
    """해커가 찾아보기 전: 모르는 칸은 모두 '?'이고, 개인키는 주인만 안다."""
    reveal["round"] += 1  # 진행 중인 애니메이션 멈추기
    for cell_id in CELLS:
        set_text(cell_id, "?")
        set_state(cell_id, "idle")
        el(cell_id).classList.remove("pop")
    set_text("s1-d", "????")
    set_state("s1-d", "idle")
    show("s1-leaked", False)
    show("s1-feedback", False)


def setup():
    cipher = pow(MESSAGE, E, N)
    set_text("s1-n", comma(N))
    set_text("s1-e", E)
    set_text("s1-m-in", MESSAGE)
    set_text("s1-c", comma(cipher))
    set_text("s1-m-out", pow(cipher, D, N))  # 개인키로 열면 다시 MESSAGE
    set_text("s1-small-n", comma(N))
    digits = str(REAL_N)
    set_text("s1-real-n", f"{digits[:10]}…{digits[-10:]}")
    set_text("s1-real-size", f"({len(digits)}자리)")
    clear()


def reset():
    """다음 사람을 위해 해커가 찾아보기 전으로 되돌린다."""
    clear()


async def crack():
    """해커처럼: 공개키 N을 3, 5, 7, … 로 차례로 나눠서 쪼개고, 찾은 p, q로 개인키를 계산한다."""
    clear()
    my_round = reveal["round"]
    p = rsa_math.find_divisor(N, 3, math.isqrt(N) + 1)
    q = N // p
    tried = len(range(3, p + 1, 2))  # 나눠 본 홀수의 개수
    d = rsa_math.private_key(p, q, E)[1]

    await asyncio.sleep(STEP_SECONDS)
    if reveal["round"] != my_round:
        return
    set_cell("s1-pq", f"{p} × {q}", "ok")  #   = 줄바꿈 없는 띄어쓰기: 칸이 좁아도 p × q는 한 줄에
    set_cell("s1-real-pq", "쪼갤 수 없음", "err")

    await asyncio.sleep(STEP_SECONDS)
    if reveal["round"] != my_round:
        return
    set_cell("s1-found-d", comma(d), "ok")
    set_cell("s1-real-d", "찾을 수 없음", "err")
    set_text("s1-d", comma(d))
    set_state("s1-d", "err")
    show("s1-leaked")
    message(
        "s1-feedback",
        f"{tried}번 나눠서 {comma(N)}{josa(N, '을', '를')} 쪼갰더니 개인키 {comma(d)}{josa(d, '이', '가')} 들통났어요! "
        f"하지만 {len(str(REAL_N))}자리 N은 쪼갤 수 없어서 개인키가 안전해요.",
        "info",
    )


@when("click", "#s1-crack")
def on_crack(event):
    run_async(crack())
