"""2단계: 계산기로 소인수분해하기 — 두~세 자리 소수 × 세 자리 소수, 시간 재기."""
import asyncio
import time

from pyscript import when

import rsa_math
from dom import comma, el, josa, message, prime_list, run_async, set_text, set_value, show, to_int, value_of

P_RANGE = (23, 997)   # 작은 쪽 소수: 두~세 자리 (너무 쉬운 11~19는 뺐어요)
Q_RANGE = (101, 997)  # 큰 쪽 소수: 세 자리
LIST_RANGE = (11, 997)  # 옆에 보여 줄 소수 목록 범위
CONTROLS = ("s2-p", "s2-q", "s2-check", "s2-plus", "s2-giveup")

state = {"p": 0, "q": 0, "n": 0, "attempts": 0, "started": 0.0, "final": 0.0, "running": False, "round": 0}


def mmss(seconds):
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"


def elapsed():
    return time.perf_counter() - state["started"]


async def tick(round_id):
    while state["running"] and state["round"] == round_id:
        set_text("s2-time", mmss(elapsed()))
        await asyncio.sleep(0.25)


def enable(on):
    for control_id in CONTROLS:
        el(control_id).disabled = not on


def start():
    p, q, n = rsa_math.random_semiprime(P_RANGE, Q_RANGE)
    state.update(p=p, q=q, n=n, attempts=0, started=time.perf_counter(), running=True, round=state["round"] + 1)
    set_text("s2-n", comma(n))
    el("s2-n").classList.remove("is-blank")
    set_text("s2-start-label", "새로운 문제")
    el("s2-start-icon").setAttribute("href", "#i-refresh")
    set_text("s2-time", "00:00")
    set_text("s2-attempts", 0)
    set_value("s2-p", "")
    set_value("s2-q", "")
    show("s2-feedback", False)
    enable(True)
    run_async(tick(state["round"]))


def finish():
    state["running"] = False
    state["final"] = elapsed()
    set_text("s2-time", mmss(state["final"]))
    enable(False)


def add_attempt():
    state["attempts"] += 1
    set_text("s2-attempts", state["attempts"])


def setup():
    prime_list("s2-primes", "s2-primes-title", "두~세 자리 소수", rsa_math.primes_between(*LIST_RANGE))
    enable(False)


def reset():
    """다음 사람을 위해 '도전 시작'을 누르기 전 상태로 되돌린다."""
    state.update(running=False, round=state["round"] + 1, attempts=0)  # 돌던 시계도 멈춘다
    set_text("s2-n", "??????")
    el("s2-n").classList.add("is-blank")
    set_text("s2-start-label", "도전 시작")
    el("s2-start-icon").setAttribute("href", "#i-play")
    set_text("s2-time", "00:00")
    set_text("s2-attempts", 0)
    set_value("s2-p", "")
    set_value("s2-q", "")
    show("s2-feedback", False)
    enable(False)


@when("click", "#s2-start")
def on_start(event):
    start()
    el("s2-p").focus()


@when("click", "#s2-plus")
def on_plus(event):
    add_attempt()


@when("submit", "#s2-form")
def on_submit(event):
    event.preventDefault()
    if not state["running"]:
        return
    blank = [box for box in ("s2-p", "s2-q") if not value_of(box)]
    if len(blank) == 1:  # 한 칸만 채우고 Enter를 누르면 빈 칸으로 넘어간다
        el(blank[0]).focus()
        return
    p, q = to_int(value_of("s2-p")), to_int(value_of("s2-q"))
    n = state["n"]
    if p is None or q is None:
        message("s2-feedback", "p와 q 칸에 숫자를 입력해 주세요.", "err")
        return
    add_attempt()
    if p * q == n and 1 not in (p, q):
        finish()
        message(
            "s2-feedback",
            f"정답! {comma(n)} = {min(p, q)} × {max(p, q)} · 걸린 시간 {mmss(state['final'])} · 시도 {state['attempts']}회",
            "ok",
        )
    elif p * q == n:  # 1 × N
        message("s2-feedback", "1 × N은 너무 쉽죠? 1이 아닌 두 소수를 찾아보세요.", "err")
    else:
        message("s2-feedback", f"{p} × {q} = {comma(p * q)} — 아직 아니에요. 계속 나눠 보세요!", "err")


@when("click", "#s2-giveup")
def on_giveup(event):
    finish()
    q = state["q"]
    message(
        "s2-feedback",
        f"정답은 {comma(state['n'])} = {state['p']} × {q}{josa(q, '이었어요', '였어요')}. 컴퓨터라면 1초도 안 걸려요 → 3단계에서 확인!",
        "info",
    )
