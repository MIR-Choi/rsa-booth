"""1단계: 암산으로 소인수분해하기 — 두 자리 소수 두 개를 곱한 N."""
from pyscript import when

import rsa_math
from dom import comma, el, josa, message, prime_list, set_text, set_value, show, to_int, value_of

PRIME_RANGE = (11, 97)  # 두 자리 소수

state = {"p": 0, "q": 0, "n": 0, "hints": 0, "done": False, "solved": 0}


def new_problem():
    p, q, n = rsa_math.random_semiprime(PRIME_RANGE)
    state.update(p=p, q=q, n=n, hints=0, done=False)
    set_text("s1-n", comma(n))
    set_text("s1-hint-label", "힌트")
    set_value("s1-p", "")
    set_value("s1-q", "")
    show("s1-feedback", False)


def setup():
    prime_list("s1-primes", "s1-primes-title", "두 자리 소수", rsa_math.primes_between(*PRIME_RANGE))
    new_problem()


def reset():
    """다음 사람을 위해 맞힌 문제 수를 0으로 하고 새 문제를 낸다."""
    state["solved"] = 0
    set_text("s1-solved", 0)
    new_problem()


@when("click", "#s1-new")
def on_new(event):
    new_problem()
    el("s1-p").focus()


@when("click", "#s1-hint")
def on_hint(event):
    p, q = state["p"], state["q"]
    state["hints"] += 1
    if state["hints"] == 1:
        tens = p // 10 * 10
        message("s1-feedback", f"힌트: 작은 소수 p는 {tens}~{tens + 9} 사이에 있어요.", "info")
        set_text("s1-hint-label", "정답 보기")
    else:
        state["done"] = True
        message("s1-feedback", f"정답은 {comma(state['n'])} = {p} × {q}입니다.", "info")


@when("click", "#s1-giveup")
def on_giveup(event):
    state["done"] = True
    q = state["q"]
    message("s1-feedback", f"정답은 {comma(state['n'])} = {state['p']} × {q}{josa(q, '이었어요', '였어요')}. '새로운 문제'로 다시 도전해 보세요!", "info")


@when("submit", "#s1-form")
def on_submit(event):
    event.preventDefault()
    blank = [box for box in ("s1-p", "s1-q") if not value_of(box)]
    if len(blank) == 1:  # 한 칸만 채우고 Enter를 누르면 빈 칸으로 넘어간다
        el(blank[0]).focus()
        return
    p, q = to_int(value_of("s1-p")), to_int(value_of("s1-q"))
    n = state["n"]
    if p is None or q is None:
        message("s1-feedback", "p와 q 칸에 숫자를 입력해 주세요.", "err")
    elif p * q != n:
        message("s1-feedback", f"아쉬워요! {p} × {q} = {comma(p * q)}{josa(p * q, '이에요', '예요')}. 다시 도전!", "err")
    elif 1 in (p, q):
        message("s1-feedback", "1 × N은 너무 쉽죠? 1이 아닌 두 소수를 찾아보세요.", "err")
    else:
        if not state["done"]:
            state["done"] = True
            state["solved"] += 1
            set_text("s1-solved", state["solved"])
        message(
            "s1-feedback",
            f"정답! {comma(n)} = {min(p, q)} × {max(p, q)} — 이 두 소수가 바로 비밀키의 재료예요.",
            "ok",
        )
