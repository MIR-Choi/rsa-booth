"""2단계: 암산으로 소인수분해하기 — 두 자리 소수 두 개를 곱한 N."""
from pyscript import when

import rsa_math
from dom import ONE_TIMES_N, answer_text, comma, el, josa, message, prime_list, read_answer, set_text, set_value, show

PRIME_RANGE = (11, 97)  # 두 자리 소수

state = {"p": 0, "q": 0, "n": 0, "hints": 0, "done": False, "solved": 0}


def new_problem():
    p, q, n = rsa_math.random_semiprime(PRIME_RANGE)
    state.update(p=p, q=q, n=n, hints=0, done=False)
    set_text("s2-n", comma(n))
    set_text("s2-hint-label", "힌트")
    set_value("s2-p", "")
    set_value("s2-q", "")
    show("s2-feedback", False)


def setup():
    prime_list("s2-primes", "s2-primes-title", "두 자리 소수", rsa_math.primes_between(*PRIME_RANGE))
    new_problem()


def reset():
    """다음 사람을 위해 맞힌 문제 수를 0으로 하고 새 문제를 낸다."""
    state["solved"] = 0
    set_text("s2-solved", 0)
    new_problem()


@when("click", "#s2-new")
def on_new(event):
    new_problem()
    el("s2-p").focus()


@when("click", "#s2-hint")
def on_hint(event):
    p, q = state["p"], state["q"]
    state["hints"] += 1
    if state["hints"] == 1:
        tens = p // 10 * 10
        message("s2-feedback", f"힌트: 작은 소수 p는 {tens}~{tens + 9} 사이에 있어요.", "info")
        set_text("s2-hint-label", "정답 보기")
    else:
        state["done"] = True
        message("s2-feedback", f"정답은 {comma(state['n'])} = {p} × {q}입니다.", "info")


@when("click", "#s2-giveup")
def on_giveup(event):
    state["done"] = True
    message("s2-feedback", f"{answer_text(state['n'], state['p'], state['q'])} '새로운 문제'로 다시 도전해 보세요!", "info")


@when("submit", "#s2-form")
def on_submit(event):
    event.preventDefault()
    answer = read_answer("s2-p", "s2-q", "s2-feedback")
    if answer is None:
        return
    p, q = answer
    n = state["n"]
    if p * q != n:
        message("s2-feedback", f"아쉬워요! {p} × {q} = {comma(p * q)}{josa(p * q, '이에요', '예요')}. 다시 도전!", "err")
    elif 1 in (p, q):
        message("s2-feedback", ONE_TIMES_N, "err")
    else:
        if not state["done"]:
            state["done"] = True
            state["solved"] += 1
            set_text("s2-solved", state["solved"])
        message(
            "s2-feedback",
            f"정답! {comma(n)} = {min(p, q)} × {max(p, q)} — 이 두 소수가 바로 개인키의 재료예요.",
            "ok",
        )
