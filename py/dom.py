"""화면(HTML)을 다루는 작은 도우미 함수들. 여러 단계가 함께 쓰는 것(답 읽기, 무작위 뽑기 등)도 여기에 둔다."""
import asyncio
import random

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


def focus_empty(*element_ids):
    """칸 중 하나만 비어 있으면 그 칸으로 커서를 옮기고 True. (한 칸만 채우고 Enter를 누르면 빈 칸으로 넘어가게)"""
    empty = [element_id for element_id in element_ids if not value_of(element_id)]
    if len(empty) == 1:
        el(empty[0]).focus()
        return True
    return False


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


def answer_text(n, p, q):
    """포기했을 때 보여 주는 정답. 예) '정답은 1,271 = 31 × 41이었어요.' / '… = 11 × 29였어요.'"""
    return f"정답은 {comma(n)} = {p} × {q}{josa(q, '이었어요', '였어요')}."


ONE_TIMES_N = "1 × N은 너무 쉽죠? 1이 아닌 두 소수를 찾아보세요."  # 2·3단계에서 1 × N을 답으로 냈을 때


def read_answer(p_id, q_id, feedback_id):
    """2·3단계의 p, q 두 칸을 숫자로 읽는다. 한 칸만 비어 있으면 그 칸으로 커서를 옮기고,
    숫자가 아닌 것이 있으면 안내 문구를 보여 준다. 둘 다 숫자일 때만 (p, q), 아니면 None."""
    if focus_empty(p_id, q_id):
        return None
    p, q = to_int(value_of(p_id)), to_int(value_of(q_id))
    if p is None or q is None:
        message(feedback_id, "p와 q 칸에 숫자를 입력해 주세요.", "err")
        return None
    return p, q


def draw_from(bag, items, last=None):
    """items 중 하나를 무작위로 뽑는다 (4단계 예시, 5단계 비밀 메시지).
    bag(리스트)에 아직 안 뽑은 것을 담아 두고 하나씩 꺼내서, 한 바퀴를 다 돌기 전에는 같은 것이 다시 나오지 않는다.
    다 꺼내면 새로 섞는데, 이때 방금 뽑은 last가 곧바로 다시 나오지 않게 한다."""
    if not bag:
        bag.extend(random.sample(items, len(items)))
        if len(bag) > 1 and bag[-1] == last:
            bag.insert(0, bag.pop())
    return bag.pop()


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
