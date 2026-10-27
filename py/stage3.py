"""3단계: 계산기로 소인수분해하기 — 두~세 자리 소수 × 세 자리 소수, 시간 재기."""
import asyncio
import time

from pyscript import when

import rsa_math
from dom import ONE_TIMES_N, answer_text, comma, el, message, prime_list, read_answer, run_async, set_text, set_value, show

P_RANGE = (23, 997)   # 작은 쪽 소수: 두~세 자리 (너무 쉬운 11~19는 뺐어요)
Q_RANGE = (101, 997)  # 큰 쪽 소수: 세 자리
LIST_RANGE = (11, 997)  # 옆에 보여 줄 소수 목록 범위
CONTROLS = ("s3-p", "s3-q", "s3-check", "s3-plus", "s3-giveup")

state = {"p": 0, "q": 0, "n": 0, "attempts": 0, "started": 0.0, "final": 0.0, "running": False, "round": 0}


def mmss(seconds):
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"


def elapsed():
    return time.perf_counter() - state["started"]


async def tick(round_id):
    while state["running"] and state["round"] == round_id:
        set_text("s3-time", mmss(elapsed()))
        await asyncio.sleep(0.25)


def enable(on):
    for control_id in CONTROLS:
        el(control_id).disabled = not on


def show_round(started):
    """새 문제를 낸 화면(started=True), 또는 '도전 시작'을 누르기 전 화면(False)."""
    set_text("s3-n", comma(state["n"]) if started else "??????")
    el("s3-n").classList.toggle("is-blank", not started)
    set_text("s3-start-label", "새로운 문제" if started else "도전 시작")
    el("s3-start-icon").setAttribute("href", "#i-refresh" if started else "#i-play")
    set_text("s3-time", "00:00")
    set_text("s3-attempts", 0)
    set_value("s3-p", "")
    set_value("s3-q", "")
    show("s3-feedback", False)
    enable(started)


def start():
    p, q, n = rsa_math.random_semiprime(P_RANGE, Q_RANGE)
    state.update(p=p, q=q, n=n, attempts=0, started=time.perf_counter(), running=True, round=state["round"] + 1)
    show_round(True)
    run_async(tick(state["round"]))


def finish():
    state["running"] = False
    state["final"] = elapsed()
    set_text("s3-time", mmss(state["final"]))
    enable(False)


def add_attempt():
    state["attempts"] += 1
    set_text("s3-attempts", state["attempts"])


def setup():
    prime_list("s3-primes", "s3-primes-title", "두~세 자리 소수", rsa_math.primes_between(*LIST_RANGE))
    enable(False)


def reset():
    """다음 사람을 위해 '도전 시작'을 누르기 전 상태로 되돌린다."""
    state.update(running=False, round=state["round"] + 1, attempts=0)  # 돌던 시계도 멈춘다
    show_round(False)


@when("click", "#s3-start")
def on_start(event):
    start()
    el("s3-p").focus()


@when("click", "#s3-plus")
def on_plus(event):
    add_attempt()


@when("submit", "#s3-form")
def on_submit(event):
    event.preventDefault()
    if not state["running"]:
        return
    answer = read_answer("s3-p", "s3-q", "s3-feedback")
    if answer is None:
        return
    p, q = answer
    n = state["n"]
    add_attempt()
    if p * q != n:
        message("s3-feedback", f"{p} × {q} = {comma(p * q)} — 아직 아니에요. 계속 나눠 보세요!", "err")
    elif 1 in (p, q):
        message("s3-feedback", ONE_TIMES_N, "err")
    else:
        finish()
        message(
            "s3-feedback",
            f"정답! {comma(n)} = {min(p, q)} × {max(p, q)} · 걸린 시간 {mmss(state['final'])} · 시도 {state['attempts']}회",
            "ok",
        )


@when("click", "#s3-giveup")
def on_giveup(event):
    finish()
    message("s3-feedback", f"{answer_text(state['n'], state['p'], state['q'])} 컴퓨터라면 1초도 안 걸려요 → 4단계에서 확인!", "info")
