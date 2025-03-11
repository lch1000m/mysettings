import os
import subprocess
import sys
from glob import glob
from pathlib import Path

# 현재 스크립트 위치로 작업 디렉토리 변경
os.chdir(os.path.dirname(os.path.abspath(__file__)))

def find_python_files(start_path='.'):
    """현재 디렉토리 및 모든 하위 디렉토리에서 .py 및 .pyw 파일을 찾습니다."""
    py_files = []
    for root, dirs, files in os.walk(start_path):
        for file in files:
            if file.endswith(('.py', '.pyw')):
                full_path = os.path.join(root, file)
                # 상대 경로로 변환
                rel_path = os.path.relpath(full_path, start_path)
                py_files.append((len(py_files) + 1, rel_path, full_path))
    return py_files

def clear_screen():
    """운영체제에 따라 화면을 지웁니다."""
    if os.name == 'nt':  # Windows
        os.system('cls')
    else:  # Mac 및 Linux
        os.system('clear')

def run_python_file(file_path):
    """Python 파일을 실행합니다."""
    try:
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.py':
            print(f"\n실행 중: python \"{file_path}\"")
            subprocess.run([sys.executable, file_path], check=True)
        elif file_ext == '.pyw':
            print(f"\n실행 중: pythonw \"{file_path}\"")
            # Windows에서는 pythonw로 실행
            if os.name == 'nt':
                subprocess.Popen(['pythonw', file_path])
            else:
                # Non-Windows에서는 일반 python으로 실행 (백그라운드)
                subprocess.Popen([sys.executable, file_path])
        
        print("\n실행 완료. 계속하려면 Enter 키를 누르세요...")
        input()
    except subprocess.CalledProcessError:
        print("\n오류가 발생했습니다. 계속하려면 Enter 키를 누르세요...")
        input()

def search_files(py_files, search_term):
    """파일 목록에서 검색어를 포함하는 파일을 찾습니다."""
    results = []
    for idx, rel_path, full_path in py_files:
        if search_term.lower() in rel_path.lower():
            results.append((len(results) + 1, rel_path, full_path))
    return results

def main():
    current_directory = os.getcwd()
    
    while True:
        clear_screen()
        print(f"======= Python 파일 실행기 =======")
        print(f"현재 디렉토리: {current_directory}")
        print("\n사용 가능한 명령:")
        print("list    - 모든 Python 파일 목록을 표시합니다")
        print("search  - 파일 이름으로 검색합니다")
        print("cd      - 작업 디렉토리를 변경합니다")
        print("run     - 파일 번호로 Python 파일을 실행합니다")
        print("exit    - 프로그램을 종료합니다")
        
        command = input("\n명령어를 입력하세요: ").strip().lower()
        
        if command == 'exit':
            break
            
        elif command == 'list':
            clear_screen()
            print(f"======= Python 파일 목록 =======")
            py_files = find_python_files()
            
            if not py_files:
                print("Python 파일을 찾을 수 없습니다.")
            else:
                for idx, rel_path, _ in py_files:
                    print(f"{idx:3d}. {rel_path}")
            
            # 파일 실행 옵션
            choice = input("\n실행할 파일 번호를 입력하거나 Enter 키를 눌러 메인 메뉴로 돌아갑니다: ")
            if choice.isdigit():
                idx = int(choice)
                if 1 <= idx <= len(py_files):
                    _, _, full_path = py_files[idx - 1]
                    run_python_file(full_path)
        
        elif command == 'search':
            search_term = input("검색어를 입력하세요: ")
            clear_screen()
            print(f"======= 검색 결과: '{search_term}' =======")
            
            py_files = find_python_files()
            results = search_files(py_files, search_term)
            
            if not results:
                print(f"'{search_term}'을(를) 포함하는 Python 파일을 찾을 수 없습니다.")
            else:
                for idx, rel_path, _ in results:
                    print(f"{idx:3d}. {rel_path}")
            
            # 파일 실행 옵션
            choice = input("\n실행할 파일 번호를 입력하거나 Enter 키를 눌러 메인 메뉴로 돌아갑니다: ")
            if choice.isdigit():
                idx = int(choice)
                if 1 <= idx <= len(results):
                    _, _, full_path = results[idx - 1]
                    run_python_file(full_path)
        
        elif command == 'cd':
            new_dir = input("새 디렉토리 경로를 입력하세요: ")
            try:
                os.chdir(new_dir)
                current_directory = os.getcwd()
            except FileNotFoundError:
                print(f"디렉토리를 찾을 수 없습니다: {new_dir}")
                input("계속하려면 Enter 키를 누르세요...")
            except PermissionError:
                print(f"디렉토리에 접근할 권한이 없습니다: {new_dir}")
                input("계속하려면 Enter 키를 누르세요...")
        
        elif command.startswith('run'):
            parts = command.split()
            if len(parts) > 1 and parts[1].isdigit():
                idx = int(parts[1])
                py_files = find_python_files()
                if 1 <= idx <= len(py_files):
                    _, _, full_path = py_files[idx - 1]
                    run_python_file(full_path)
                else:
                    print(f"유효하지 않은 파일 번호입니다: {idx}")
                    input("계속하려면 Enter 키를 누르세요...")
            else:
                try:
                    # 'list' 명령어 실행 후 선택
                    clear_screen()
                    print(f"======= Python 파일 목록 =======")
                    py_files = find_python_files()
                    
                    if not py_files:
                        print("Python 파일을 찾을 수 없습니다.")
                    else:
                        for idx, rel_path, _ in py_files:
                            print(f"{idx:3d}. {rel_path}")
                    
                    choice = input("\n실행할 파일 번호를 입력하세요: ")
                    if choice.isdigit():
                        idx = int(choice)
                        if 1 <= idx <= len(py_files):
                            _, _, full_path = py_files[idx - 1]
                            run_python_file(full_path)
                        else:
                            print(f"유효하지 않은 파일 번호입니다: {idx}")
                            input("계속하려면 Enter 키를 누르세요...")
                except Exception as e:
                    print(f"오류 발생: {str(e)}")
                    input("계속하려면 Enter 키를 누르세요...")
        
        else:
            print("알 수 없는 명령어입니다.")
            input("계속하려면 Enter 키를 누르세요...")

if __name__ == "__main__":
    main()
