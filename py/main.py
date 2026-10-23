"""RSA 암호 해독 체험하기 — 시작 파일.

시작 화면과 탭(단계) 전환을 맡고, 각 단계(stage1~4)를 준비한다.
주소 끝에 #stage-3 처럼 붙이면 시작 화면 없이 그 단계가 바로 열린다 (페이지를 연 뒤에 바꿔도 된다).
"""
from pyscript import document, when, window
from pyscript.ffi import create_proxy

import stage1
import stage2
import stage3
import stage4
from dom import el, set_text

STAGES = ("1", "2", "3", "4")


def show_stage(stage):
    for tab in document.querySelectorAll(".tab"):
        active = tab.getAttribute("data-stage") == stage
        tab.classList.toggle("is-active", active)
        tab.setAttribute("aria-selected", "true" if active else "false")
    for s in STAGES:
        el(f"stage-{s}").hidden = s != stage


def show_intro(visible):
    el("intro").classList.toggle("is-done", not visible)
    el("app").inert = visible  # 시작 화면 뒤의 버튼이 키보드로 눌리지 않게


@when("click", ".tab")
def on_tab(event):
    show_stage(event.currentTarget.getAttribute("data-stage"))


@when("click", "#start")
def on_start(event):
    show_stage("1")
    show_intro(False)


@when("click", "#home")
def on_home(event):
    """처음 화면으로 돌아가면서 모든 단계를 처음 상태로 되돌린다 (다음 사람을 위해)."""
    event.preventDefault()
    window.history.replaceState(None, "", window.location.pathname)  # 주소의 #stage-N 지우기
    for module in (stage1, stage2, stage3, stage4):
        module.reset()
    show_intro(True)


def warm_fonts():
    """글꼴은 화면에 나온 글자의 조각만 받는다. 숨어 있는 단계의 글자와 비밀 메시지 글자도 미리 받아 두면,
    단계를 처음 열 때 글꼴이 바뀌며 깜빡이지 않고, 나중에 인터넷이 끊겨도 글꼴이 그대로 나온다."""
    text = el("app").textContent + "".join(stage4.SECRET_MESSAGES)
    for weight in (400, 600, 700, 800):
        document.fonts.load(f"{weight} 16px Pretendard", text)


def open_from_address():
    """주소가 #stage-N 이면 시작 화면 없이 그 단계를 연다. 맞으면 True."""
    stage = window.location.hash.replace("#stage-", "")
    if stage in STAGES:
        show_stage(stage)
        show_intro(False)
        return True
    return False


for module in (stage1, stage2, stage3, stage4):
    module.setup()

if not open_from_address():
    show_stage("1")
window.addEventListener("hashchange", create_proxy(lambda event: open_from_address()))

set_text("start-label", "시작하기")
el("start").disabled = False
el("intro").classList.add("is-ready")
warm_fonts()
