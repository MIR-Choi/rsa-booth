"""화면(HTML)을 다루는 작은 도우미 함수들."""
import asyncio

from pyscript import document

_tasks = set()


def el(element_id):
    return document.getElementById(element_id)


def set_text(element_id, text):
    el(element_id).textContent = str(text)


def set_html(element_id, markup):
    el(element_id).innerHTML = markup  # 숫자처럼 안전한 값만 넣는다 (사용자 입력은 set_text로)


def value_of(element_id):
    return el(element_id).value.strip()


def set_value(element_id, value):
    el(element_id).value = str(value)


def show(element_id, visible=True):
    el(element_id).hidden = not visible


def set_state(element_id, state):
    """CSS의 [data-state="..."] 로 색을 바꾼다. (ok / err / info / run / idle)"""
    el(element_id).setAttribute("data-state", state)


def message(element_id, text, state="info"):
    """안내 문구를 보여주고 살짝 튀어나오는 애니메이션을 다시 재생한다."""
    box = el(element_id)
    box.textContent = text
    box.setAttribute("data-state", state)
    box.hidden = False
    box.classList.remove("pop")
    _ = box.offsetWidth  # 애니메이션을 처음부터 다시 재생하기 위한 reflow
    box.classList.add("pop")


def to_int(text):
    """'1,271' 처럼 쉼표가 있어도 숫자로 바꾼다. 숫자가 아니면 None."""
    cleaned = text.replace(",", "").replace(" ", "")
    if not (cleaned.isascii() and cleaned.isdigit()):
        return None
    try:
        return int(cleaned)
    except ValueError:  # 너무 긴 숫자
        return None


def comma(n):
    return f"{n:,}"


# 숫자를 소리 내어 읽을 때 끝 글자의 받침 (None = 받침 없음). 을/를, 으로/로 같은 조사를 고를 때 쓴다.
_DIGIT_BATCHIM = {0: "ㅇ", 1: "ㄹ", 2: None, 3: "ㅁ", 4: None, 5: None, 6: "ㄱ", 7: "ㄹ", 8: "ㄹ", 9: None}  # 영 일 이 삼 사 오 육 칠 팔 구
_UNIT_BATCHIM = {1: "ㅂ", 2: "ㄱ", 3: "ㄴ"}             # 십 백 천
_BIG_UNIT_BATCHIM = {1: "ㄴ", 2: "ㄱ", 3: None, 4: "ㅇ"}  # 만 억 조 경


def batchim(n):
    """예) 761(칠백육십일) → 'ㄹ', 1,804(천팔백사) → None, 3,240(삼천이백사십) → 'ㅂ', 1,000,000(백만) → 'ㄴ'"""
    if n == 0:
        return "ㅇ"
    zeros = 0
    while n % 10 == 0:
        n //= 10
        zeros += 1
    if zeros == 0:
        return _DIGIT_BATCHIM[n % 10]
    if zeros < 4:
        return _UNIT_BATCHIM[zeros]
    return _BIG_UNIT_BATCHIM.get(zeros // 4)


def josa(n, after_batchim, otherwise):
    """숫자 n 뒤에 붙일 조사. 예) josa(761, '을', '를') → '을', josa(29, '이었어요', '였어요') → '였어요'
    '으로/로'는 ㄹ 받침 뒤에도 '로'를 쓴다. 예) josa(1848, '으로', '로') → '로' (천팔백사십팔로)"""
    sound = batchim(n)
    if after_batchim == "으로":
        return otherwise if sound in (None, "ㄹ") else after_batchim
    return otherwise if sound is None else after_batchim


def prime_list(list_id, title_id, title, primes):
    """옆에 작게 보여 주는 소수 목록."""
    set_text(title_id, f"{title} {len(primes)}개")
    set_html(list_id, "".join(f"<span>{p}</span>" for p in primes))


def run_async(coro):
    """일반 이벤트 함수 안에서 async 작업을 시작한다."""
    task = asyncio.ensure_future(coro)
    _tasks.add(task)
    task.add_done_callback(_tasks.discard)
    return task
