"""RSA 암호 해독 체험관 — 시작 파일.

탭(단계) 전환을 맡고, 각 단계(stage1~4)를 준비한다.
주소 끝에 #stage-3 처럼 붙이면 그 단계가 바로 열린다.
"""
from pyscript import document, when, window

import stage1
import stage2
import stage3
import stage4
from dom import el

STAGES = ("1", "2", "3", "4")


def show_stage(stage):
    for tab in document.querySelectorAll(".tab"):
        active = tab.getAttribute("data-stage") == stage
        tab.classList.toggle("is-active", active)
        tab.setAttribute("aria-selected", "true" if active else "false")
    for s in STAGES:
        el(f"stage-{s}").hidden = s != stage
    window.history.replaceState(None, "", f"#stage-{stage}")


@when("click", ".tab")
def on_tab(event):
    show_stage(event.currentTarget.getAttribute("data-stage"))


for module in (stage1, stage2, stage3, stage4):
    module.setup()

start = window.location.hash.replace("#stage-", "")
show_stage(start if start in STAGES else "1")
el("loading").classList.add("is-done")
