import os
import subprocess
import sys
from pathlib import Path

def list_python_files(current_path='.'):
    """현재 폴더의 Python 파일과 하위 폴더를 표시합니다."""
    # 현재 경로의 절대 경로 구하기
    abs_path = os.path.abspath(current_path)
    
    # 현재 경로 표시
    print(f"\n현재 위치: {abs_path}\n")
    
    # 폴더 내의 항목들을 모두 수집
    items = os.listdir(current_path)
    
    # Python 파일과 폴더 분리
    py_files = []
    folders = []
    
    for item in items:
        item_path = os.path.join(current_path, item)
        if os.path.isfile(item_path) and (item.endswith('.py') or item.endswith('.pyw')):
            py_files.append(item)
        elif os.path.isdir(item_path):
            folders.append(item)
    
    # Python 파일 출력
    if py_files:
        print("=== Python 파일 (.py, .pyw) ===")
        for idx, file in enumerate(py_files):
            print(f"{idx + 1:3d}. {file}")
    else:
        print("현재 폴더에 Python 파일이 없습니다.")
    
    # 하위 폴더 출력
    if folders:
        print("\n=== 하위 폴더 ===")
        for idx, folder in enumerate(folders):
            # 폴더 내부의 Python 파일 개수 확인
            folder_path = os.path.join(current_path, folder)
            py_count = count_python_files(folder_path)
            print(f"{idx + 1 + len(py_files):3d}. {folder} ({py_count}개의 Python 파일)")
    else:
        print("\n하위 폴더가 없습니다.")
    
    return py_files, folders

def count_python_files(folder_path):
    """폴더 내의 Python 파일 개수를 반환합니다."""
    count = 0
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.endswith('.py') or file.endswith('.pyw'):
                count += 1
    return count

def run_python_file(file_path):
    """Python 파일을 새 CMD 창에서 실행합니다."""
    try:
        file_ext = os.path.splitext(file_path)[1].lower()
        
        # 파일의 절대 경로 구하기
        abs_path = os.path.abspath(file_path)
        
        # 파일이 있는 디렉토리
        file_dir = os.path.dirname(abs_path)
        
        if os.name == 'nt':  # Windows
            if file_ext == '.py':
                # 새 CMD 창에서 Python 파일 실행
                cmd = f'start cmd.exe /K "cd /d "{file_dir}" && python "{abs_path}"'
                os.system(cmd)
            elif file_ext == '.pyw':
                # 새 CMD 창에서 PythonW 실행 (GUI 프로그램)
                cmd = f'start cmd.exe /K "cd /d "{file_dir}" && pythonw "{abs_path}"'
                os.system(cmd)
        else:  # Mac 및 Linux
            if file_ext == '.py':
                # 새 터미널에서 Python 파일 실행
                cmd = f'gnome-terminal -- bash -c "cd \'{file_dir}\' && python3 \'{abs_path}\'; exec bash"'
                os.system(cmd)
            elif file_ext == '.pyw':
                # 새 터미널에서 Python 실행 (GUI 프로그램)
                cmd = f'gnome-terminal -- bash -c "cd \'{file_dir}\' && python3 \'{abs_path}\'; exec bash"'
                os.system(cmd)
        
        print(f"\n'{os.path.basename(file_path)}'을(를) 새 창에서 실행했습니다.")
    except Exception as e:
        print(f"\n오류 발생: {str(e)}")

def clear_screen():
    """운영체제에 따라 화면을 지웁니다."""
    if os.name == 'nt':  # Windows
        os.system('cls')
    else:  # Mac 및 Linux
        os.system('clear')

def main():
    current_path = '.'
    
    while True:
        clear_screen()
        print("======= Python 파일 브라우저 =======")
        
        # 현재 폴더의 Python 파일과 하위 폴더 표시
        py_files, folders = list_python_files(current_path)
        
        print("\n명령어:")
        print("- 숫자 입력: 해당 항목 선택 (파일 실행 또는 폴더 진입)")
        print("- b: 뒤로 가기 (상위 폴더로)")
        print("- q: 종료")
        
        choice = input("\n선택: ").strip().lower()
        
        if choice == 'q':
            print("프로그램을 종료합니다.")
            break
            
        elif choice == 'b':
            # 상위 폴더로 이동
            if os.path.abspath(current_path) != os.path.abspath(os.path.dirname(current_path)):
                current_path = os.path.join(current_path, '..')
            else:
                print("이미 최상위 폴더입니다.")
                input("계속하려면 Enter 키를 누르세요...")
        
        elif choice.isdigit():
            idx = int(choice)
            
            # Python 파일 선택
            if 1 <= idx <= len(py_files):
                file_name = py_files[idx - 1]
                file_path = os.path.join(current_path, file_name)
                run_python_file(file_path)
                input("\n계속하려면 Enter 키를 누르세요...")
            
            # 폴더 선택
            elif len(py_files) < idx <= len(py_files) + len(folders):
                folder_idx = idx - len(py_files) - 1
                folder_name = folders[folder_idx]
                current_path = os.path.join(current_path, folder_name)
            
            else:
                print("잘못된 선택입니다.")
                input("계속하려면 Enter 키를 누르세요...")
        
        else:
            print("잘못된 입력입니다.")
            input("계속하려면 Enter 키를 누르세요...")

if __name__ == "__main__":
    main()
