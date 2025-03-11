import os
import sys
import psutil
import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

class ProcessManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("프로세스 관리자")
        self.root.geometry("1000x600")
        self.root.minsize(800, 500)
        
        # 아이콘 설정 (Windows에서만 작동)
        if os.name == 'nt':
            self.root.iconbitmap(default='NONE')
        
        # 프로세스 데이터를 저장할 변수
        self.processes = []
        self.selected_pid = None
        self.auto_refresh = False
        self.auto_refresh_thread = None
        self.stop_thread = threading.Event()
        
        # UI 생성
        self.create_widgets()
        
        # 초기 데이터 로드
        self.refresh_process_list()
        
    def create_widgets(self):
        # 메인 프레임
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 상단 컨트롤 프레임
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 새로고침 버튼
        refresh_btn = ttk.Button(control_frame, text="새로고침", command=self.refresh_process_list, width=15)
        refresh_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # 자동 새로고침 체크박스
        self.auto_refresh_var = tk.BooleanVar()
        auto_refresh_check = ttk.Checkbutton(control_frame, text="자동 새로고침 (3초)", 
                                             variable=self.auto_refresh_var,
                                             command=self.toggle_auto_refresh)
        auto_refresh_check.pack(side=tk.LEFT, padx=5)
        
        # 검색 프레임
        search_frame = ttk.Frame(control_frame)
        search_frame.pack(side=tk.RIGHT)
        
        ttk.Label(search_frame, text="검색:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *args: self.filter_processes())
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=5)
        
        # 상태 레이블
        self.status_var = tk.StringVar()
        self.status_var.set("준비")
        status_label = ttk.Label(main_frame, textvariable=self.status_var, anchor=tk.W)
        status_label.pack(fill=tk.X, side=tk.BOTTOM, pady=(5, 0))
        
        # 프로세스 목록 프레임
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # 트리뷰 생성
        columns = ("pid", "name", "status", "cpu", "memory", "created")
        self.process_tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        
        # 열 헤더 정의
        self.process_tree.heading("pid", text="PID")
        self.process_tree.heading("name", text="프로세스 이름")
        self.process_tree.heading("status", text="상태")
        self.process_tree.heading("cpu", text="CPU 사용량 (%)")
        self.process_tree.heading("memory", text="메모리 사용량 (MB)")
        self.process_tree.heading("created", text="생성 시간")
        
        # 열 너비 설정
        self.process_tree.column("pid", width=70, anchor=tk.CENTER)
        self.process_tree.column("name", width=250)
        self.process_tree.column("status", width=100, anchor=tk.CENTER)
        self.process_tree.column("cpu", width=120, anchor=tk.CENTER)
        self.process_tree.column("memory", width=150, anchor=tk.CENTER)
        self.process_tree.column("created", width=150, anchor=tk.CENTER)
        
        # 스크롤바 추가
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.process_tree.yview)
        self.process_tree.configure(yscrollcommand=scrollbar.set)
        
        # 트리뷰와 스크롤바 배치
        self.process_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 트리뷰 선택 이벤트 바인딩
        self.process_tree.bind("<<TreeviewSelect>>", self.on_process_select)
        
        # 버튼 프레임
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 종료 버튼
        self.kill_btn = ttk.Button(button_frame, text="프로세스 종료", command=self.kill_process, state=tk.DISABLED)
        self.kill_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # 일시 중지/재실행 버튼
        self.pause_btn = ttk.Button(button_frame, text="일시 중지", command=self.toggle_process_state, state=tk.DISABLED)
        self.pause_btn.pack(side=tk.LEFT)
        
    def refresh_process_list(self):
        """프로세스 목록 새로고침"""
        self.status_var.set("프로세스 목록 로딩 중...")
        
        # 트리뷰 비우기
        for item in self.process_tree.get_children():
            self.process_tree.delete(item)
        
        # 새로운 프로세스 목록 가져오기
        self.processes = []
        for proc in psutil.process_iter(['pid', 'name', 'status', 'cpu_percent', 'memory_info', 'create_time']):
            try:
                process_info = proc.info
                # 메모리를 MB 단위로 변환
                memory_mb = process_info['memory_info'].rss / (1024 * 1024)
                
                # 생성 시간을 일반 시간 형식으로 변환
                create_time = datetime.fromtimestamp(process_info['create_time']).strftime('%Y-%m-%d %H:%M:%S')
                
                self.processes.append({
                    'pid': process_info['pid'],
                    'name': process_info['name'],
                    'status': process_info['status'],
                    'cpu': process_info['cpu_percent'],
                    'memory': memory_mb,
                    'created': create_time
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        # 검색 필터 적용
        self.filter_processes()
        
        # 버튼 비활성화
        self.kill_btn.config(state=tk.DISABLED)
        self.pause_btn.config(state=tk.DISABLED)
        self.selected_pid = None
        
        # 상태 갱신
        self.status_var.set(f"총 {len(self.processes)} 개의 프로세스 로드됨. 마지막 업데이트: {datetime.now().strftime('%H:%M:%S')}")
    
    def filter_processes(self):
        """검색어로 프로세스 필터링"""
        # 트리뷰 비우기
        for item in self.process_tree.get_children():
            self.process_tree.delete(item)
        
        search_text = self.search_var.get().lower()
        
        # 프로세스 추가
        for proc in self.processes:
            if search_text == "" or search_text in proc['name'].lower() or search_text in str(proc['pid']):
                values = (
                    proc['pid'],
                    proc['name'],
                    proc['status'],
                    f"{proc['cpu']:.1f}",
                    f"{proc['memory']:.1f}",
                    proc['created']
                )
                self.process_tree.insert("", tk.END, values=values)
    
    def on_process_select(self, event):
        """프로세스 선택 처리"""
        selected_items = self.process_tree.selection()
        if selected_items:
            selected_item = selected_items[0]
            pid = int(self.process_tree.item(selected_item, "values")[0])
            self.selected_pid = pid
            
            # 버튼 활성화
            self.kill_btn.config(state=tk.NORMAL)
            
            # 프로세스 상태 확인 후 일시 중지/재실행 버튼 레이블 설정
            try:
                proc = psutil.Process(pid)
                status = proc.status()
                
                if status == psutil.STATUS_STOPPED:
                    self.pause_btn.config(text="재실행", state=tk.NORMAL)
                else:
                    self.pause_btn.config(text="일시 중지", state=tk.NORMAL)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                self.pause_btn.config(state=tk.DISABLED)
    
    def kill_process(self):
        """선택한 프로세스 종료"""
        if self.selected_pid:
            try:
                proc = psutil.Process(self.selected_pid)
                proc_name = proc.name()
                
                if messagebox.askyesno("프로세스 종료", f"프로세스 '{proc_name}' (PID: {self.selected_pid})를 종료하시겠습니까?"):
                    proc.terminate()
                    
                    # 1초 대기 후 프로세스가 종료되었는지 확인
                    time.sleep(1)
                    if proc.is_running():
                        # 강제 종료
                        proc.kill()
                    
                    messagebox.showinfo("프로세스 종료", f"프로세스 '{proc_name}'가 종료되었습니다.")
                    self.refresh_process_list()
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                messagebox.showerror("오류", f"프로세스를 종료할 수 없습니다: {str(e)}")
    
    def toggle_process_state(self):
        """프로세스 일시 중지/재실행 토글"""
        if self.selected_pid:
            try:
                proc = psutil.Process(self.selected_pid)
                status = proc.status()
                
                if status == psutil.STATUS_STOPPED:
                    # 재실행
                    proc.resume()
                    messagebox.showinfo("프로세스 재실행", f"프로세스 '{proc.name()}'가 재실행되었습니다.")
                else:
                    # 일시 중지
                    proc.suspend()
                    messagebox.showinfo("프로세스 일시 중지", f"프로세스 '{proc.name()}'가 일시 중지되었습니다.")
                
                self.refresh_process_list()
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                messagebox.showerror("오류", f"프로세스 상태를 변경할 수 없습니다: {str(e)}")
    
    def toggle_auto_refresh(self):
        """자동 새로고침 토글"""
        self.auto_refresh = self.auto_refresh_var.get()
        
        if self.auto_refresh:
            # 이미 실행 중인 스레드가 있으면 중지
            if self.auto_refresh_thread and self.auto_refresh_thread.is_alive():
                self.stop_thread.set()
                self.auto_refresh_thread.join()
            
            # 새로운 스레드 시작
            self.stop_thread.clear()
            self.auto_refresh_thread = threading.Thread(target=self.auto_refresh_task)
            self.auto_refresh_thread.daemon = True
            self.auto_refresh_thread.start()
        else:
            # 스레드 중지
            if self.auto_refresh_thread and self.auto_refresh_thread.is_alive():
                self.stop_thread.set()
    
    def auto_refresh_task(self):
        """자동 새로고침 작업 (별도 스레드)"""
        while not self.stop_thread.is_set():
            time.sleep(3)  # 3초 간격으로 새로고침
            
            if not self.stop_thread.is_set():
                # GUI 스레드에서 새로고침 실행
                self.root.after(0, self.refresh_process_list)
    
    def on_closing(self):
        """프로그램 종료 처리"""
        # 스레드 종료
        if self.auto_refresh_thread and self.auto_refresh_thread.is_alive():
            self.stop_thread.set()
            self.auto_refresh_thread.join()
        
        self.root.destroy()

if __name__ == "__main__":
    # GUI 실행
    root = tk.Tk()
    app = ProcessManagerApp(root)
    
    # 창 종료 이벤트 처리
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # 메인 루프 시작
    root.mainloop()
