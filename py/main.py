"""RSA 암호 해독 체험하기 — 시작 파일.

시작 화면과 탭(단계) 전환을 맡고, 각 단계(stage1~4)를 준비한다.
주소 끝에 #stage-3 처럼 붙이면 시작 화면 없이 그 단계가 바로 열린다 (페이지를 연 뒤에 바꿔도 된다).
준비가 끝나면 글꼴을 미리 받고, 인터넷 없이도 열리도록 파일을 저장해 두고(sw.js), 화면이 꺼지지 않게 한다.
"""
from pyscript import document, when, window
from pyscript.ffi import create_proxy, to_js

import stage1
import stage2
import stage3
import stage4
from dom import el, run_async, set_text

STAGES = ("1", "2", "3", "4")
screen = {"lock": None}  # 화면 꺼짐 방지 (다른 창으로 가면 브라우저가 풀고, 돌아오면 다시 건다)


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
    run_async(keep_screen_on())  # 브라우저에 따라 버튼을 누른 뒤에만 허락되기도 해서 한 번 더


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


async def save_for_offline():
    """한 번 열고 나면 인터넷이 없어도 열리도록, 서비스 워커(sw.js)에게 지금까지 받은 파일을 저장해 달라고 한다.
    내 컴퓨터(localhost)에서 열 때는 하지 않는다 — 같은 주소로 여는 다른 프로젝트에 끼어들지 않게."""
    workers = getattr(window.navigator, "serviceWorker", None)  # https 주소(와 localhost)에서만 있다
    if workers is None or window.location.hostname in ("localhost", "127.0.0.1", "[::1]"):
        return
    try:
        await workers.register("./sw.js")
    except Exception:  # 개인 정보 보호 창 등에서는 거절될 수 있다
        return
    worker = (await workers.ready).active
    page = window.location.href.split("#")[0]
    urls = [page, window.URL.new("./", page).href]
    urls += [entry.name for entry in window.performance.getEntriesByType("resource")]
    worker.postMessage(to_js(urls))


async def keep_screen_on():
    """부스 화면이 저절로 꺼지지 않게 한다. 이 페이지가 화면에 보이는 동안만이고, 다른 창으로 가면 저절로 풀린다."""
    wake_lock = getattr(window.navigator, "wakeLock", None)
    held = screen["lock"] is not None and not screen["lock"].released
    if wake_lock is None or held or document.visibilityState != "visible":
        return
    try:
        screen["lock"] = await wake_lock.request("screen")
    except Exception:  # 배터리 절약 모드 등에서는 거절될 수 있다
        pass


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
document.addEventListener("visibilitychange", create_proxy(lambda event: run_async(keep_screen_on())))

set_text("start-label", "시작하기")
el("start").disabled = False
el("intro").classList.add("is-ready")
warm_fonts()
run_async(save_for_offline())
run_async(keep_screen_on())
