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
