import os
import re
import time
import subprocess
import psutil
import win32gui
import win32process
import keyboard
import atexit  # 프로그램 종료 시 정리 작업을 위해 추가

# 현재 스크립트 위치로 작업 디렉토리 변경
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# AutoHotkey 실행 파일 경로 (환경에 맞게 수정)
AHK_EXECUTABLE = r"C:\Program Files\AutoHotkey\v2\AutoHotkey64.exe"

# filename_conversion 사전: 특정 .ahk 파일에 대해 window title과 매칭할 정규식 패턴을 지정
filename_conversion = {
    "youtube.ahk": r"Youtube - Chrome$",
    "youtube_watch.ahk": r".{15,} - YouTube - Chrome",
    "Grok.ahk": r".+ - Grok - Chrome$",
    "claude.ahk": r".+ - claude - Chrome$",
    "Gemini.ahk": [r"gemini - Chrome$", "쌍둥이자리 - Chrome$"],
    "missav.ahk": [r"missav", r"^[A-Za-z]{2,6}-\d{2,6}"],
}

# 제외할 AHK 파일 목록 (항상 실행되어야 하는 스크립트)
EXCLUDED_SCRIPTS = {"ActiveWindowBlink.ahk"}

# 전역 변수: 모드 상태와 현재 실행 중인 AHK 프로세스/스크립트 추적
# Mode 1: 기본 모드 - 현 코드 기능을 함
# Mode 2: 디버깅 모드 - 현 상태에서 서버 프로그램 일시 중지
# Mode 3: 글쓰기 모드 - 모든 ahk 파일 모두 종료 후 프로그램 일시 중지
CURRENT_MODE = 1
current_ahk_process = None
current_script = None
excluded_processes = {}  # 항상 실행되는 스크립트 프로세스를 추적하기 위한 dict

def get_active_window_info():
    """현재 활성 윈도우의 프로세스 이름과 타이틀을 반환합니다."""
    hwnd = win32gui.GetForegroundWindow()
    title = win32gui.GetWindowText(hwnd)
    _, pid = win32process.GetWindowThreadProcessId(hwnd)
    try:
        proc = psutil.Process(pid)
        exe_name = proc.name()
    except Exception:
        exe_name = ""
    return exe_name, title

def kill_running_ahk(proc_obj):
    """실행 중인 AHK 프로세스가 있으면 해당 프로세스만 종료합니다."""
    if proc_obj and proc_obj.poll() is None:
        try:
            proc_obj.terminate()
            proc_obj.wait(timeout=5)
            print("현재 AHK 프로세스가 정상적으로 종료됨")
        except subprocess.TimeoutExpired:
            proc_obj.kill()
            print("현재 AHK 프로세스가 강제로 종료됨")
        except Exception as e:
            print(f"AHK 프로세스 종료 중 오류 발생: {e}")

def launch_script(script_path):
    """지정된 .ahk 스크립트를 AHK_EXECUTABLE을 통해 실행합니다."""
    return subprocess.Popen([AHK_EXECUTABLE, script_path])

def find_matching_script(exe_name, window_title):
    """
    현재 폴더(비재귀적)에서 active window의 exe 이름(확장자 제거)이 포함된 .ahk 파일이 있으면 반환.
    하위 폴더에서 매칭되는 파일이 없으면, 그 폴더 내에 기본 스크립트가 있으면 이를 반환합니다.
    """
    exe_base = exe_name.lower().replace(".exe", "")
    current_dir = os.getcwd()

    for file in os.listdir(current_dir):
        if (file.lower().endswith(".ahk") and exe_base in file.lower() and
                file.lower() not in (x.lower() for x in EXCLUDED_SCRIPTS)):
            return os.path.join(current_dir, file)

    target_subfolder = next((os.path.join(current_dir, entry) for entry in os.listdir(current_dir)
                             if os.path.isdir(os.path.join(current_dir, entry)) and entry.lower() == exe_base), None)

    if target_subfolder:
        for file in os.listdir(target_subfolder):
            if file.lower().endswith(".ahk") and file.lower() not in (x.lower() for x in EXCLUDED_SCRIPTS):
                pattern = filename_conversion.get(file, re.escape(os.path.splitext(file)[0]))
                if isinstance(pattern, (list, tuple)):
                    if any(re.search(p, window_title, re.IGNORECASE) for p in pattern):
                        return os.path.join(target_subfolder, file)
                elif re.search(pattern, window_title, re.IGNORECASE):
                    return os.path.join(target_subfolder, file)
        basic_path = os.path.join(target_subfolder, "basic.ahk")
        if os.path.exists(basic_path) and os.path.basename(basic_path).lower() not in (x.lower() for x in EXCLUDED_SCRIPTS):
            return basic_path
    return None

def switch_to_mode1():
    """Mode 1: 기본 모드 - 현 코드 기능을 함"""
    global CURRENT_MODE
    if CURRENT_MODE != 1:
        CURRENT_MODE = 1
        print("Mode 1 활성화: 기본 모드")
        # 항상 실행 스크립트 재시작 (필요한 경우)
        restart_excluded_scripts()

def switch_to_mode2():
    """Mode 2: 디버깅 모드 - 현 상태에서 서버 프로그램 일시 중지"""
    global CURRENT_MODE
    if CURRENT_MODE != 2:
        CURRENT_MODE = 2
        print("Mode 2 활성화: 디버깅 모드 (현재 스크립트는 유지되지만 새로운 스크립트 실행 안 함)")

def switch_to_mode3():
    """Mode 3: 글쓰기 모드 - 모든 ahk 파일 모두 종료 후 프로그램 일시 중지"""
    global CURRENT_MODE, current_ahk_process, current_script
    if CURRENT_MODE != 3:
        CURRENT_MODE = 3
        print("Mode 3 활성화: 글쓰기 모드 (모든 AHK 파일 종료)")
        
        # 현재 실행 중인 일반 스크립트 종료
        kill_running_ahk(current_ahk_process)
        current_ahk_process = None
        current_script = None
        
        # 항상 실행 스크립트도 종료
        terminate_excluded_scripts()

def launch_excluded_scripts():
    """EXCLUDED_SCRIPTS에 속한 모든 스크립트를 시작합니다."""
    global excluded_processes
    current_dir = os.getcwd()

    # 현재 폴더에서 EXCLUDED_SCRIPTS에 있는 스크립트 찾기
    for file in os.listdir(current_dir):
        if file.lower() in (x.lower() for x in EXCLUDED_SCRIPTS):
            script_path = os.path.join(current_dir, file)
            try:
                process = launch_script(script_path)
                excluded_processes[file] = process
                print(f"항상 실행 스크립트 시작: {file}")
            except Exception as e:
                print(f"항상 실행 스크립트 시작 오류 ({file}): {e}")

    # 하위 폴더 검색
    for root, dirs, files in os.walk(current_dir):
        for file in files:
            if file.lower() in (x.lower() for x in EXCLUDED_SCRIPTS) and file not in excluded_processes:
                script_path = os.path.join(root, file)
                try:
                    process = launch_script(script_path)
                    excluded_processes[file] = process
                    print(f"항상 실행 스크립트 시작: {file} (경로: {root})")
                except Exception as e:
                    print(f"항상 실행 스크립트 시작 오류 ({file}): {e}")

def terminate_excluded_scripts():
    """항상 실행 스크립트를 종료합니다."""
    global excluded_processes
    
    for script, process in list(excluded_processes.items()):
        if process and process.poll() is None:
            try:
                process.terminate()
                process.wait(timeout=3)
                print(f"항상 실행 스크립트 종료됨: {script}")
            except subprocess.TimeoutExpired:
                process.kill()
                print(f"항상 실행 스크립트 강제 종료됨: {script}")
            except Exception as e:
                print(f"항상 실행 스크립트 종료 오류 ({script}): {e}")
        excluded_processes.pop(script, None)

def restart_excluded_scripts():
    """항상 실행 스크립트를 재시작합니다."""
    terminate_excluded_scripts()
    launch_excluded_scripts()

def terminate_all_scripts():
    """모든 실행 중인 스크립트를 종료합니다."""
    global current_ahk_process
    
    # 현재 실행 중인 일반 스크립트 종료
    kill_running_ahk(current_ahk_process)
    current_ahk_process = None
    
    # 항상 실행 스크립트 종료
    terminate_excluded_scripts()

def main():
    global current_ahk_process, current_script, CURRENT_MODE

    # 종료 시 모든 스크립트 종료를 위한 이벤트 등록
    atexit.register(terminate_all_scripts)

    # 모드 1로 시작 (기본 모드)
    switch_to_mode1()

    # 핫키 등록
    keyboard.add_hotkey("f1", switch_to_mode1)  # F1: Mode 1 (기본 모드)
    keyboard.add_hotkey("f2", switch_to_mode2)  # F2: Mode 2 (디버깅 모드)
    keyboard.add_hotkey("f3", switch_to_mode3)  # F3: Mode 3 (글쓰기 모드)

    try:
        while True:
            if CURRENT_MODE == 1:  # 기본 모드
                exe_name, window_title = get_active_window_info()
                new_script = find_matching_script(exe_name, window_title)

                if new_script != current_script:
                    kill_running_ahk(current_ahk_process)
                    current_ahk_process = None
                    current_script = None

                    if new_script:
                        try:
                            current_ahk_process = launch_script(new_script)
                            current_script = new_script
                            print(f"실행: {new_script} (프로세스: {exe_name}, 타이틀: {window_title})")
                        except Exception as e:
                            print(f"AHK 스크립트 실행 오류 ({new_script}): {e}")
                    else:
                        print(f"해당하지 않는 프로세스 ({exe_name}). AHK 스크립트 실행 없음.")
            
            # Mode 2 및 Mode 3에서는 새로운 스크립트를 실행하지 않음
            # (디버깅 모드에서는 현재 스크립트 유지, 글쓰기 모드에서는 모든 스크립트 종료)
            
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("프로그램 종료 요청...")
    finally:
        # 종료 시 모든 스크립트 종료
        terminate_all_scripts()

if __name__ == "__main__":
    main()
