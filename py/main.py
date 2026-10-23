"""RSA 암호 해독 체험관 — 시작 파일.

시작 화면과 탭(단계) 전환을 맡고, 각 단계(stage1~4)를 준비한다.
주소 끝에 #stage-3 처럼 붙이면 시작 화면 없이 그 단계가 바로 열린다.
"""
from pyscript import document, when, window

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


for module in (stage1, stage2, stage3, stage4):
    module.setup()

start = window.location.hash.replace("#stage-", "")
if start in STAGES:
    show_stage(start)
    show_intro(False)
else:
    show_stage("1")

set_text("start-label", "시작하기")
el("start").disabled = False
el("intro").classList.add("is-ready")
