"""3단계: 컴퓨터에게 소인수분해 시키기 — 난이도마다 정해진 예시 중 하나를 무작위로 뽑아 분해해 본다.

컴퓨터도 사람과 똑같이 3, 5, 7, 9, … 를 차례로 나눠 본다.
다만 1초에 수백만 번 나눌 수 있을 뿐이다. 그래도 RSA-2048의 617자리 N 앞에서는 소용이 없다.
"""
import asyncio
import math
import random
import time

from pyscript import document, when

import rsa_examples
import rsa_math
from dom import comma, el, run_async, set_html, set_state, set_text, show

TIME_LIMITS = {"rsa2048": 5, "rsa8192": 10}  # 큰 N은 컴퓨터가 난이도마다 이 시간(초)만큼 계산해 보고 포기한다
HUMAN_SECONDS = 5     # 사람이 계산기로 한 번 나누는 데 걸린다고 가정한 시간(초)
FRAME_SECONDS = 0.1   # 이만큼 계산할 때마다 화면을 새로 그린다

# 난이도 목록. 예시 (p, q)는 rsa_examples.py에 정해 두었다.
LEVELS = {
    "small": {
        "pairs": rsa_examples.LEVEL1,
        "note": "세 자리 소수 두 개를 곱한 수예요. 2단계에서 계산기로 풀던 크기죠.",
    },
    "medium": {
        "pairs": rsa_examples.LEVEL2,
        "note": "다섯~여섯 자리 소수 두 개를 곱한 수예요. 사람이 계산기로 풀면 며칠에서 몇 주가 걸려요.",
    },
    "rsa2048": {
        "pairs": rsa_examples.LEVEL3,
        "note": f"실제 2048비트 RSA 키의 N이에요. 지금 가장 널리 쓰이는 크기라서, 컴퓨터에게 {TIME_LIMITS['rsa2048']}초만 줘 볼게요.",
    },
    "rsa8192": {
        "pairs": rsa_examples.LEVEL4,
        "note": f"실제 8192비트 RSA 키의 N이에요. 흔히 쓰는 RSA-2048보다 4배 긴 키입니다. 컴퓨터에게 {TIME_LIMITS['rsa8192']}초만 줘 볼게요.",
    },
}
HUGE = tuple(TIME_LIMITS)  # 시간 제한을 두고, 숫자를 작은 글씨로 보여 주는 난이도

bags = {}  # 난이도 → 아직 안 뽑은 예시 번호들 (한 바퀴를 다 돌기 전에는 같은 예시가 다시 나오지 않게)
current = {"level": "small", "index": None, "busy": False}  # index None = 아직 아무 예시도 안 보여 줌


def seconds_text(sec):
    if sec < 0.0001:
        return "0.0001초 미만"
    if sec < 1:
        return f"{sec:.4f}초"
    return f"{sec:.2f}초"


def duration_text(sec):
    for unit, size in (("년", rsa_math.SECONDS_PER_YEAR), ("일", 86400), ("시간", 3600), ("분", 60)):
        if sec >= size:
            return f"약 {sec / size:,.1f}{unit}"
    return f"약 {sec:.0f}초"


def power_html(log10_value):
    """아주 큰 수를 '3.2 × 10²⁸⁵' 꼴로."""
    exp = math.floor(log10_value)
    return f"{10 ** (log10_value - exp):.1f} × 10<sup>{exp}</sup>"


# ── 예시 뽑기 ───────────────────────────────────────────

def draw(level):
    """준비된 예시 중 하나를 무작위로 뽑는다. 한 바퀴를 다 돌면 다시 섞는다."""
    bag = bags.get(level)
    if not bag:
        bag = list(range(len(LEVELS[level]["pairs"])))
        random.shuffle(bag)
        if level == current["level"] and len(bag) > 1 and bag[-1] == current["index"]:
            bag.insert(0, bag.pop())  # 방금 본 예시가 곧바로 다시 나오지 않게
        bags[level] = bag
    return bag.pop()


def current_example():
    p, q = LEVELS[current["level"]]["pairs"][current["index"]]
    return {"n": p * q, "p": p, "q": q}


# ── 화면 그리기 ─────────────────────────────────────────

def reset_result():
    set_text("s3-time", "-")
    set_text("s3-count", "-")
    set_text("s3-verdict", "대기 중")
    set_state("s3-verdict", "idle")
    el("s3-bar").style.width = "0%"
    set_html("s3-detail", '<p class="empty">왼쪽 버튼을 누르면 컴퓨터가 계산을 시작해요.</p>')
    show("s3-reveal", False)


def render():
    level = current["level"]
    for option in document.querySelectorAll(".level-opt"):
        active = option.getAttribute("data-level") == level
        option.classList.toggle("is-active", active)
        option.setAttribute("aria-checked", "true" if active else "false")
    n = current_example()["n"]
    huge = level in HUGE
    el("s3-n").classList.toggle("is-huge", huge)
    set_text("s3-n", n if huge else comma(n))
    set_text("s3-size", f"{len(str(n))}자리 · {n.bit_length()}비트")
    set_text("s3-pool", f"준비된 예시 {len(LEVELS[level]['pairs'])}개 중 무작위로 뽑았어요")
    set_text("s3-note", LEVELS[level]["note"])
    reset_result()


def show_success(n, p, tried):
    set_text("s3-verdict", "해독 성공")
    set_state("s3-verdict", "ok")
    el("s3-bar").style.width = "100%"
    set_html(
        "s3-detail",
        f'<div class="equation">{comma(n)} = {p} × {n // p}</div>'
        f"<p>사람이 계산기로 한 번 나누는 데 {HUMAN_SECONDS}초 걸린다면 → "
        f"<b>{duration_text(tried * HUMAN_SECONDS)}</b></p>",
    )


def show_failure(n, tried, compute, limit):
    set_text("s3-verdict", "해독 불가능")
    set_state("s3-verdict", "err")
    rate = tried / compute
    log_needed = math.log10((math.isqrt(n) - 1) // 2)  # 3부터 √N까지 홀수의 개수
    log_years = log_needed - math.log10(rate) - math.log10(rsa_math.SECONDS_PER_YEAR)
    log_human = log_needed + math.log10(HUMAN_SECONDS) - math.log10(rsa_math.SECONDS_PER_YEAR)
    log_universe = log_years - math.log10(rsa_math.UNIVERSE_AGE_YEARS)
    set_html(
        "s3-detail",
        f"<p>{limit}초 동안 <b>{comma(tried)}번</b> 나눠 봤지만(1초에 약 {comma(int(rate))}번) "
        f"인수를 하나도 찾지 못했어요.</p>"
        f'<ul class="estimates">'
        f"<li><span>끝까지 나눠 보려면</span><b>최대 {power_html(log_needed)}번</b></li>"
        f"<li><span>이 컴퓨터로는</span><b>약 {power_html(log_years)}년</b></li>"
        f"<li><span>우주 나이(138억 년)와 비교</span><b>약 {power_html(log_universe)}배</b></li>"
        f"<li><span>사람이 계산기로 하면</span><b>약 {power_html(log_human)}년</b></li>"
        f"</ul>",
    )
    show("s3-reveal")


# ── 컴퓨터의 소인수분해 ─────────────────────────────────

async def attack():
    """3, 5, 7, 9, … 로 차례로 나눠 본다. 중간중간 화면을 갱신하기 위해 조금씩 끊어서 계산한다."""
    level = current["level"]
    n = current_example()["n"]
    limit = math.isqrt(n)
    give_up_after = TIME_LIMITS.get(level)
    reset_result()
    set_text("s3-verdict", "계산 중…")
    set_state("s3-verdict", "run")
    set_html("s3-detail", '<p class="empty">3, 5, 7, 9, … 차례로 나눠 보는 중…</p>')
    await asyncio.sleep(0.05)

    d, tried, compute, chunk = 3, 0, 0.0, 2000
    found = None
    while d <= limit:  # N은 홀수끼리의 곱이라 2로는 나눌 필요가 없다
        step = chunk
        if give_up_after:  # 마지막 조각은 남은 시간만큼만 계산해서 제한 시간을 딱 채운다
            step = max(100, min(chunk, int(chunk * (give_up_after - compute) / FRAME_SECONDS)))
        span = range(d, min(d + 2 * step, limit + 1), 2)
        t0 = time.perf_counter()
        found = rsa_math.find_divisor(n, span.start, span.stop)
        spent = time.perf_counter() - t0
        compute += spent
        if found:
            tried += (found - d) // 2 + 1
            break
        tried += len(span)
        d += 2 * len(span)

        set_text("s3-count", f"{comma(tried)}번")
        set_text("s3-time", seconds_text(compute))
        if give_up_after:
            ratio = compute / give_up_after  # 화면을 그리는 시간은 빼고, 실제로 계산한 시간만 센다
            el("s3-bar").style.width = f"{min(ratio, 1) * 100:.1f}%"
            if ratio >= 0.999:
                break
        else:
            el("s3-bar").style.width = f"{d / limit * 100:.1f}%"
        chunk = max(1000, min(2_000_000, int(step * FRAME_SECONDS / max(spent, 1e-4))))
        await asyncio.sleep(0.01)

    set_text("s3-count", f"{comma(tried)}번")
    set_text("s3-time", seconds_text(compute))
    if found:
        show_success(n, found, tried)
    else:
        show_failure(n, tried, compute, give_up_after)


def set_busy(on):
    current["busy"] = on
    for button_id in ("s3-run", "s3-draw"):
        el(button_id).disabled = on
    for button in document.querySelectorAll(".level-opt"):
        button.disabled = on


async def run():
    if current["busy"]:
        return
    set_busy(True)
    try:
        await attack()
    finally:
        set_busy(False)


def show_example(level):
    """그 난이도의 예시를 하나 뽑아서 보여 준다."""
    if current["busy"]:
        return
    current["index"] = draw(level)
    current["level"] = level
    render()


def setup():
    show_example("small")


@when("click", ".level-opt")
def on_level(event):
    level = event.currentTarget.getAttribute("data-level")
    if level != current["level"]:
        show_example(level)


@when("click", "#s3-draw")
def on_draw(event):
    show_example(current["level"])


@when("click", "#s3-run")
def on_run(event):
    run_async(run())


@when("click", "#s3-reveal")
def on_reveal(event):
    ex = current_example()
    set_html(
        "s3-answers",
        f'<div class="r-label">p ({len(str(ex["p"]))}자리)</div><div class="bignum">{ex["p"]}</div>'
        f'<div class="r-label">q ({len(str(ex["q"]))}자리)</div><div class="bignum">{ex["q"]}</div>',
    )
    el("s3-dialog").showModal()
