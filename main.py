import tkinter as tk
import requests
from datetime import datetime
import threading
import time
import re
import json
import os
import copy

class GoldPriceApp:
    # 노트 매핑 상수
    NOTE_MAPPING = {
        'Gold24k-3.75g': ('gold_buy_note', 'gold_sell_note'),
        'Gold18k-3.75g': ('gold18k_buy_note', 'gold18k_sell_note'),
        'Gold14k-3.75g': ('gold14k_buy_note', 'gold14k_sell_note'),
        'Platinum-3.75g': ('platinum_buy_note', 'platinum_sell_note'),
        'Silver-3.75g': ('silver_buy_note', 'silver_sell_note')
    }
    
    # API 필드 매핑
    API_FIELD_MAPPING = {
        'Gold24k-3.75g': ('s_pure', 'per_s_pure', 'turm_s_pure', 'p_pure', 'per_p_pure', 'turm_p_pure'),
        'Gold18k-3.75g': ('s_18k', 'per_s_18k', 'turm_s_18k', 'p_18k', 'per_p_18k', 'turm_p_18k'),
        'Gold14k-3.75g': ('s_14k', 'per_s_14k', 'turm_s_14k', 'p_14k', 'per_p_14k', 'turm_p_14k'),
        'Platinum-3.75g': ('s_white', 'per_s_white', 'turm_s_white', 'p_white', 'per_p_white', 'turm_p_white'),
        'Silver-3.75g': ('s_silver', 'per_s_silver', 'turm_s_silver', 'p_silver', 'per_p_silver', 'turm_p_silver')
    }
    
    # 색상 상수
    COLOR_UP = '#E24A4A'
    COLOR_DOWN = '#4A90E2'
    COLOR_ERROR = '#E24A4A'
    COLOR_TEXT = '#FFFFFF'
    COLOR_BG = '#1a1a1a'
    COLOR_CARD_BG = '#2a2a2a'
    COLOR_SEPARATOR = '#333333'
    COLOR_BUTTON_PRIMARY = '#4A90E2'
    COLOR_BUTTON_PRIMARY_ACTIVE = '#357ABD'
    COLOR_BUTTON_SECONDARY = '#666666'
    COLOR_BUTTON_SECONDARY_ACTIVE = '#555555'
    COLOR_BUTTON_DANGER_ACTIVE = '#C73939'
    COLOR_BUTTON_ADMIN = '#444444'
    COLOR_BUTTON_ADMIN_ACTIVE = '#666666'
    COLOR_TEXT_SECONDARY = '#AAAAAA'
    COLOR_TEXT_TERTIARY = '#888888'
    COLOR_TEXT_QUATERNARY = '#999999'
    COLOR_CHANGE_DEFAULT = '#5AA5FF'
    
    # 폰트 상수
    FONT_FAMILY = '맑은 고딕'
    FONT_SIZE_TITLE = 18
    FONT_SIZE_TITLE_DIALOG = 14
    FONT_SIZE_HEADER = 10
    FONT_SIZE_BODY = 9
    FONT_SIZE_INFO = 11
    FONT_SIZE_PRICE = 16
    FONT_SIZE_PRICE_SMALL = 12
    FONT_SIZE_CHANGE = 9
    FONT_SIZE_CHANGE_SMALL = 7
    FONT_SIZE_NOTE = 8
    FONT_SIZE_BUTTON = 9
    FONT_SIZE_ADMIN_ICON = 14
    FONT_SIZE_HIDE_BUTTON = 7
    
    # 레이아웃 상수 (필수적인 것만)
    WINDOW_WIDTH = 600
    WINDOW_HEIGHT = 650
    WINDOW_MIN_HEIGHT = 520
    DIALOG_WIDTH = 480
    DIALOG_HEIGHT = 600
    
    # 애니메이션 상수
    ANIMATION_STEPS = 15
    ANIMATION_DURATION = 400
    
    # 기본 설정값 (전체)
    DEFAULT_SETTINGS = {
        'hidden_items': {
            'buy': {'Gold18k-3.75g', 'Gold14k-3.75g'},
            'sell': set()
        },
        'custom_texts': {
            'title': '한국금거래소 시세',
            'buy_header': '내가 살 때 (VAT포함)',
            'sell_header': '내가 팔 때 (금방금방 앱 기준)',
            'hide_text': '제품시세적용',
            'error_message': '일시적 조회 오류',
            'gold_buy_note': '',
            'gold_sell_note': '',
            'gold18k_buy_note': '',
            'gold18k_sell_note': '',
            'gold14k_buy_note': '',
            'gold14k_sell_note': '',
            'platinum_buy_note': '',
            'platinum_sell_note': '(자사백금바기준)',
            'silver_buy_note': '',
            'silver_sell_note': '(자사실버바기준)'
        },
        'update_interval': 10,
        'error_timeout': 3
    }
    
    def __init__(self, root):
        self.root = root
        
        self.root.title("한국금거래소 시세조회 v1.0.0")
        self.root.configure(bg=self.COLOR_BG)
        self.root.geometry(f"{self.WINDOW_WIDTH}x{self.WINDOW_HEIGHT}")
        self.root.minsize(self.WINDOW_WIDTH, self.WINDOW_MIN_HEIGHT)
        
        self.is_running = True
        self.current_window_height = self.WINDOW_HEIGHT
        self.previous_data = {}
        
        # 설정 로드
        self.settings = self.load_settings()
        self.hidden_items = self.settings['hidden_items']
        self.custom_texts = self.settings['custom_texts']
        self.update_interval = self.settings['update_interval']
        self.error_timeout = self.settings['error_timeout']  # 분 단위
        self.countdown = self.update_interval  # countdown은 update_interval로 초기화
        self.admin_mode = False  # 관리자 모드 기본값
        
        # API 상태 추적
        self.last_success_time = time.time()
        self.last_update_datetime = datetime.now()
        self.api_error = False
        
        self.setup_ui()
        self.root.after(100, self.start_auto_update)
    
    def load_settings(self):
        """설정 파일 로드"""
        # 파일이 없으면 기본값 반환
        if not os.path.exists('settings.json'):
            return copy.deepcopy(self.DEFAULT_SETTINGS)
        
        try:
            with open('settings.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 기본값 복사
            settings = copy.deepcopy(self.DEFAULT_SETTINGS)
            
            # hidden_items를 set으로 변환
            if 'hidden_buy' in data or 'hidden_sell' in data:
                settings['hidden_items'] = {
                    'buy': set(data.get('hidden_buy', [])),
                    'sell': set(data.get('hidden_sell', []))
                }
            
            # custom_texts는 기본값과 merge (파일의 값이 우선)
            if 'custom_texts' in data:
                settings['custom_texts'].update(data['custom_texts'])
            
            # update_interval과 error_timeout
            if 'update_interval' in data:
                settings['update_interval'] = data['update_interval']
            if 'error_timeout' in data:
                settings['error_timeout'] = data['error_timeout']
            
            return settings
        except:
            # 오류 발생 시 기본값 반환
            return copy.deepcopy(self.DEFAULT_SETTINGS)
    
    def save_settings(self):
        """설정 파일 저장"""
        try:
            with open('settings.json', 'w', encoding='utf-8') as f:
                json.dump({
                    'hidden_buy': list(self.hidden_items['buy']),
                    'hidden_sell': list(self.hidden_items['sell']),
                    'custom_texts': self.custom_texts,
                    'update_interval': self.update_interval,
                    'error_timeout': self.error_timeout
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"설정 저장 오류: {e}")
    
    def toggle_item_visibility(self, key, side):
        """항목 표시/숨김 토글
        Args:
            key: 항목 키 (예: 'Gold18k-3.75g')
            side: 'buy' 또는 'sell'
        """
        if key in self.hidden_items[side]:
            self.hidden_items[side].remove(key)
        else:
            self.hidden_items[side].add(key)
        self.save_settings()
        
        # UI 즉시 업데이트
        if hasattr(self, 'latest_data') and self.latest_data:
            self.update_ui(self.latest_data)
    
    def toggle_admin_mode(self):
        """관리자 모드 토글"""
        self.admin_mode = not self.admin_mode
        
        # 모든 카드의 Hide 버튼 표시/숨김
        for card in self.cards.values():
            for btn_attr in ['buy_hide_btn', 'sell_hide_btn']:
                if hasattr(card, btn_attr):
                    btn = getattr(card, btn_attr)
                    if self.admin_mode:
                        btn.pack(side=tk.LEFT, padx=(5, 0))
                    else:
                        btn.pack_forget()
        
        # 설정 버튼 표시/숨김
        if self.admin_mode:
            self.settings_btn.pack(side=tk.LEFT, padx=(5, 0))
        else:
            self.settings_btn.pack_forget()
    
    def open_settings_dialog(self):
        """설정 다이얼로그 열기"""
        dialog = tk.Toplevel(self.root)
        dialog.title("설정")
        dialog.configure(bg=self.COLOR_BG)
        
        # 메인 창의 위치와 크기 가져오기
        self.root.update_idletasks()
        main_x = self.root.winfo_x()
        main_y = self.root.winfo_y()
        main_width = self.root.winfo_width()
        
        # 설정 창을 메인 창 오른쪽에 배치
        dialog_x = main_x + main_width + 10
        dialog_y = main_y
        
        dialog.geometry(f"{self.DIALOG_WIDTH}x{self.DIALOG_HEIGHT}+{dialog_x}+{dialog_y}")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 상단 헤더 프레임 (제목만)
        header_frame = tk.Frame(dialog, bg=self.COLOR_BG)
        header_frame.pack(fill=tk.X, padx=20, pady=(10, 5))
        
        # 제목
        title_label = tk.Label(
            header_frame,
            text="커스텀 설정",
            font=(self.FONT_FAMILY, self.FONT_SIZE_TITLE_DIALOG, 'bold'),
            fg=self.COLOR_TEXT,
            bg=self.COLOR_BG
        )
        title_label.pack(anchor='w')
        
        # 버튼 프레임 (제목 아래)
        button_frame = tk.Frame(dialog, bg=self.COLOR_BG)
        button_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        # 스크롤 가능한 프레임
        canvas = tk.Canvas(dialog, bg=self.COLOR_BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(dialog, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.COLOR_BG)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True, padx=20)
        scrollbar.pack(side="right", fill="y")
        
        entries = {}
        labels = [
            ('title', '제목'),
            ('buy_header', '살 때 헤더'),
            ('sell_header', '팔 때 헤더'),
            ('hide_text', 'Hide 텍스트'),
            ('error_message', '에러 메시지'),
            ('update_interval', '업데이트 간격 (초)'),
            ('error_timeout', 'API 에러 타임아웃 (분)'),
            ('', ''),  # 구분선
            ('gold_buy_note', '순금 - 살 때 노트'),
            ('gold_sell_note', '순금 - 팔 때 노트'),
            ('gold18k_buy_note', '18K금 - 살 때 노트'),
            ('gold18k_sell_note', '18K금 - 팔 때 노트'),
            ('gold14k_buy_note', '14K금 - 살 때 노트'),
            ('gold14k_sell_note', '14K금 - 팔 때 노트'),
            ('platinum_buy_note', '백금 - 살 때 노트'),
            ('platinum_sell_note', '백금 - 팔 때 노트'),
            ('silver_buy_note', '은 - 살 때 노트'),
            ('silver_sell_note', '은 - 팔 때 노트')
        ]
        
        for idx, (key, label_text) in enumerate(labels):
            if key == '':  # 구분선
                separator = tk.Frame(scrollable_frame, bg=self.COLOR_SEPARATOR, height=2)
                separator.grid(row=idx, column=0, columnspan=2, sticky='ew', pady=10, padx=10)
                continue
            
            label = tk.Label(
                scrollable_frame,
                text=label_text,
                font=(self.FONT_FAMILY, self.FONT_SIZE_BODY),
                fg=self.COLOR_TEXT,
                bg=self.COLOR_BG
            )
            label.grid(row=idx, column=0, sticky='w', pady=3, padx=(10, 0))
            
            entry = tk.Entry(
                scrollable_frame,
                font=(self.FONT_FAMILY, self.FONT_SIZE_BODY),
                bg=self.COLOR_CARD_BG,
                fg=self.COLOR_TEXT,
                insertbackground=self.COLOR_TEXT,
                relief=tk.FLAT,
                width=35
            )
            if key == 'update_interval':
                entry.insert(0, str(self.update_interval))
            elif key == 'error_timeout':
                entry.insert(0, str(self.error_timeout))
            else:
                entry.insert(0, self.custom_texts[key])
            entry.grid(row=idx, column=1, sticky='ew', pady=3, padx=(10, 10))
            entries[key] = entry
        
        scrollable_frame.columnconfigure(1, weight=1)
        
        def reset_to_default():
            """기본값 복원"""
            default = self.DEFAULT_SETTINGS
            # custom_texts 복원
            for key, value in default['custom_texts'].items():
                if key in entries:
                    entries[key].delete(0, tk.END)
                    entries[key].insert(0, value)
            # update_interval, error_timeout 복원
            entries['update_interval'].delete(0, tk.END)
            entries['update_interval'].insert(0, str(default['update_interval']))
            entries['error_timeout'].delete(0, tk.END)
            entries['error_timeout'].insert(0, str(default['error_timeout']))
        
        def save_and_close():
            # 숫자 설정 저장 (업데이트 간격, 에러 타임아웃)
            for setting_key, default_value in [('update_interval', 'update_interval'), ('error_timeout', 'error_timeout')]:
                try:
                    value = int(entries[setting_key].get())
                    if value < 1:
                        value = self.DEFAULT_SETTINGS[default_value]
                    setattr(self, setting_key, value)
                    if setting_key == 'update_interval':
                        self.countdown = value
                except:
                    default = self.DEFAULT_SETTINGS[default_value]
                    setattr(self, setting_key, default)
                    if setting_key == 'update_interval':
                        self.countdown = default
            
            # 텍스트 설정 저장
            for key, entry in entries.items():
                if key not in ['update_interval', 'error_timeout']:
                    self.custom_texts[key] = entry.get()
            
            self.save_settings()
            
            # UI 업데이트
            self.title_label.config(text=self.custom_texts['title'])
            self.buy_header_label.config(text=self.custom_texts['buy_header'])
            self.sell_header_label.config(text=self.custom_texts['sell_header'])
            
            # 각 카드의 노트 업데이트
            for key, card in self.cards.items():
                if key in self.NOTE_MAPPING:
                    for side in ['buy', 'sell']:
                        note_key = self.NOTE_MAPPING[key][0 if side == 'buy' else 1]
                        note_attr = f'{side}_note'
                        if hasattr(card, note_attr):
                            note_text = self.custom_texts[note_key]
                            note_widget = getattr(card, note_attr)
                            if note_text:
                                note_widget.config(text=note_text)
                                note_widget.pack(anchor='w', pady=(2, 0))
                            else:
                                note_widget.pack_forget()
            
            if hasattr(self, 'latest_data') and self.latest_data:
                self.update_ui(self.latest_data)
            
            dialog.destroy()
        
        # 버튼들을 버튼 프레임에 추가 (왼쪽 정렬)
        save_btn = tk.Button(
            button_frame,
            text="저장",
            font=(self.FONT_FAMILY, self.FONT_SIZE_BUTTON),
            fg=self.COLOR_TEXT,
            bg=self.COLOR_BUTTON_PRIMARY,
            activebackground=self.COLOR_BUTTON_PRIMARY_ACTIVE,
            activeforeground=self.COLOR_TEXT,
            relief=tk.FLAT,
            cursor='hand2',
            padx=15,
            pady=5,
            command=save_and_close
        )
        save_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        cancel_btn = tk.Button(
            button_frame,
            text="취소",
            font=(self.FONT_FAMILY, self.FONT_SIZE_BUTTON),
            fg=self.COLOR_TEXT,
            bg=self.COLOR_BUTTON_SECONDARY,
            activebackground=self.COLOR_BUTTON_SECONDARY_ACTIVE,
            activeforeground=self.COLOR_TEXT,
            relief=tk.FLAT,
            cursor='hand2',
            padx=15,
            pady=5,
            command=dialog.destroy
        )
        cancel_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        default_btn = tk.Button(
            button_frame,
            text="기본값 복원",
            font=(self.FONT_FAMILY, self.FONT_SIZE_BUTTON),
            fg=self.COLOR_TEXT,
            bg=self.COLOR_ERROR,
            activebackground=self.COLOR_BUTTON_DANGER_ACTIVE,
            activeforeground=self.COLOR_TEXT,
            relief=tk.FLAT,
            cursor='hand2',
            padx=15,
            pady=5,
            command=reset_to_default
        )
        default_btn.pack(side=tk.LEFT)
        
    def setup_ui(self):
        self.main_frame = tk.Frame(self.root, bg=self.COLOR_BG)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)
        
        header_frame = tk.Frame(self.main_frame, bg=self.COLOR_BG)
        header_frame.pack(fill=tk.X, pady=(0, 8))
        
        self.title_label = tk.Label(
            header_frame,
            text=self.custom_texts['title'],
            font=(self.FONT_FAMILY, self.FONT_SIZE_TITLE, 'bold'),
            fg=self.COLOR_TEXT,
            bg=self.COLOR_BG
        )
        self.title_label.pack(side=tk.LEFT)
        
        # 왼쪽 버튼 컨테이너 (제목 제외)
        left_buttons = tk.Frame(header_frame, bg=self.COLOR_BG)
        left_buttons.pack(side=tk.LEFT, padx=(10, 0))
        
        # 관리자 모드 토글 버튼 (톱니바퀴)
        admin_btn = tk.Button(
            left_buttons,
            text="⚙",
            font=(self.FONT_FAMILY, self.FONT_SIZE_ADMIN_ICON),
            fg=self.COLOR_TEXT_TERTIARY,
            bg=self.COLOR_BG,
            activebackground=self.COLOR_CARD_BG,
            activeforeground=self.COLOR_TEXT,
            relief=tk.FLAT,
            cursor='hand2',
            padx=5,
            pady=0,
            command=self.toggle_admin_mode
        )
        admin_btn.pack(side=tk.LEFT)
        
        # 설정 버튼 (처음엔 숨김)
        self.settings_btn = tk.Button(
            left_buttons,
            text="설정",
            font=(self.FONT_FAMILY, self.FONT_SIZE_BUTTON),
            fg=self.COLOR_TEXT,
            bg=self.COLOR_BUTTON_ADMIN,
            activebackground=self.COLOR_BUTTON_ADMIN_ACTIVE,
            activeforeground=self.COLOR_TEXT,
            relief=tk.FLAT,
            cursor='hand2',
            padx=10,
            pady=3,
            command=self.open_settings_dialog
        )
        # 기본적으로 숨김 상태
        
        info_frame = tk.Frame(header_frame, bg=self.COLOR_BG)
        info_frame.pack(side=tk.RIGHT)
        
        # 시간과 카운트다운을 한 줄에 배치
        time_container = tk.Frame(info_frame, bg=self.COLOR_BG)
        time_container.pack(anchor='e')
        
        self.date_label = tk.Label(
            time_container,
            text="",
            font=(self.FONT_FAMILY, self.FONT_SIZE_INFO),
            fg=self.COLOR_TEXT_SECONDARY,
            bg=self.COLOR_BG,
            width=20,
            anchor='e'
        )
        self.date_label.pack(side=tk.LEFT)
        
        self.countdown_label = tk.Label(
            time_container,
            text="",
            font=(self.FONT_FAMILY, self.FONT_SIZE_INFO),
            fg=self.COLOR_TEXT_TERTIARY,
            bg=self.COLOR_BG,
            width=5,
            anchor='w'
        )
        self.countdown_label.pack(side=tk.LEFT, padx=(5, 0))
        
        # 테이블 헤더
        table_header_frame = tk.Frame(self.main_frame, bg=self.COLOR_BG)
        table_header_frame.pack(fill=tk.X, pady=(0, 5))
        
        # 왼쪽 빈 공간 (항목명 위치)
        left_spacer = tk.Frame(table_header_frame, bg=self.COLOR_BG, width=150)
        left_spacer.pack(side=tk.LEFT)
        
        # 가격 헤더 컨테이너
        prices_header = tk.Frame(table_header_frame, bg=self.COLOR_BG)
        prices_header.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        
        # 살 때 헤더
        buy_header_frame = tk.Frame(prices_header, bg=self.COLOR_BG)
        buy_header_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.buy_header_label = tk.Label(
            buy_header_frame,
            text=self.custom_texts['buy_header'],
            font=(self.FONT_FAMILY, self.FONT_SIZE_HEADER, 'bold'),
            fg=self.COLOR_TEXT,
            bg=self.COLOR_BG
        )
        self.buy_header_label.pack(anchor='w')
        
        # 팔 때 헤더
        sell_header_frame = tk.Frame(prices_header, bg=self.COLOR_BG)
        sell_header_frame.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        
        self.sell_header_label = tk.Label(
            sell_header_frame,
            text=self.custom_texts['sell_header'],
            font=(self.FONT_FAMILY, self.FONT_SIZE_HEADER, 'bold'),
            fg=self.COLOR_TEXT,
            bg=self.COLOR_BG
        )
        self.sell_header_label.pack(anchor='w')
        
        self.prices_frame = tk.Frame(self.main_frame, bg=self.COLOR_BG)
        self.prices_frame.pack(fill=tk.BOTH, expand=True)
        
        self.cards = {}
        items = [
            ('순금시세', 'Gold24k-3.75g'),
            ('18K 금시세', 'Gold18k-3.75g'),
            ('14K 금시세', 'Gold14k-3.75g'),
            ('백금시세', 'Platinum-3.75g'),
            ('은시세', 'Silver-3.75g')
        ]
        
        for idx, (name, key) in enumerate(items):
            card = self.create_price_card(self.prices_frame, name, key)
            if idx == len(items) - 1:
                card.pack(fill=tk.BOTH, expand=True)
            else:
                card.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
            self.cards[key] = card
        
        self.root.bind('<Configure>', self.on_window_resize)
    
    def create_price_side(self, parent, key, side, column, padx):
        """가격 측면(buy/sell) UI 생성"""
        frame = tk.Frame(parent, bg=self.COLOR_CARD_BG)
        frame.grid(row=0, column=column, sticky='nsew', padx=padx)
        
        # 가격과 Hide 버튼을 같은 행에 배치
        price_frame = tk.Frame(frame, bg=self.COLOR_CARD_BG)
        price_frame.pack(anchor='w', pady=(0, 1), fill=tk.X)
        
        price_label = tk.Label(
            price_frame,
            text="0원",
            font=(self.FONT_FAMILY, self.FONT_SIZE_PRICE, 'bold'),
            fg=self.COLOR_TEXT,
            bg=self.COLOR_CARD_BG,
            anchor='w'
        )
        price_label.pack(side=tk.LEFT, anchor='w')
        
        hide_btn = tk.Button(
            price_frame,
            text="Hide",
            font=(self.FONT_FAMILY, self.FONT_SIZE_HIDE_BUTTON),
            fg=self.COLOR_TEXT,
            bg=self.COLOR_BUTTON_ADMIN,
            activebackground=self.COLOR_BUTTON_ADMIN_ACTIVE,
            activeforeground=self.COLOR_TEXT,
            relief=tk.FLAT,
            cursor='hand2',
            padx=3,
            pady=0,
            command=lambda: self.toggle_item_visibility(key, side)
        )
        
        change_label = tk.Label(
            frame,
            text="0% ▼ 0",
            font=(self.FONT_FAMILY, self.FONT_SIZE_CHANGE),
            fg=self.COLOR_CHANGE_DEFAULT,
            bg=self.COLOR_CARD_BG,
            anchor='w'
        )
        change_label.pack(anchor='w', fill=tk.X)
        
        note_label = tk.Label(
            frame,
            text="",
            font=(self.FONT_FAMILY, self.FONT_SIZE_NOTE),
            fg=self.COLOR_TEXT_SECONDARY,
            bg=self.COLOR_CARD_BG
        )
        if key in self.NOTE_MAPPING:
            note_key = self.NOTE_MAPPING[key][0 if side == 'buy' else 1]
            note_text = self.custom_texts[note_key]
            if note_text:
                note_label.config(text=note_text)
                note_label.pack(anchor='w', pady=(2, 0))
        
        return frame, {
            'price': price_label,
            'change': change_label,
            'hide_btn': hide_btn,
            'note': note_label
        }
    
    def create_price_card(self, parent, title, key):
        card_frame = tk.Frame(parent, bg=self.COLOR_CARD_BG, relief=tk.FLAT, bd=0)
        
        # 전체 컨테이너를 좌우로 분할
        main_container = tk.Frame(card_frame, bg=self.COLOR_CARD_BG)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 왼쪽: 제목 영역 (고정 너비)
        title_frame = tk.Frame(main_container, bg=self.COLOR_CARD_BG, width=150)
        title_frame.pack(side=tk.LEFT, fill=tk.Y)
        title_frame.pack_propagate(False)  # 너비 고정
        
        title_label = tk.Label(
            title_frame,
            text=title,
            font=(self.FONT_FAMILY, self.FONT_SIZE_PRICE_SMALL, 'bold'),
            fg=self.COLOR_TEXT,
            bg=self.COLOR_CARD_BG,
            anchor='w'
        )
        title_label.pack(anchor='w')
        
        unit_label = tk.Label(
            title_frame,
            text=key,
            font=(self.FONT_FAMILY, self.FONT_SIZE_NOTE),
            fg=self.COLOR_TEXT_QUATERNARY,
            bg=self.COLOR_CARD_BG,
            anchor='w'
        )
        unit_label.pack(anchor='w')
        
        # 오른쪽: 가격 영역
        prices_container = tk.Frame(main_container, bg=self.COLOR_CARD_BG)
        prices_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Grid 레이아웃으로 정확히 50:50 분할
        prices_container.columnconfigure(0, weight=1, uniform='column')
        prices_container.columnconfigure(1, weight=1, uniform='column')
        
        # buy/sell 섹션 생성
        buy_frame, buy_widgets = self.create_price_side(prices_container, key, 'buy', 0, (0, 5))
        sell_frame, sell_widgets = self.create_price_side(prices_container, key, 'sell', 1, (5, 0))
        
        # 위젯들을 card_frame에 연결
        card_frame.buy_price = buy_widgets['price']
        card_frame.buy_change = buy_widgets['change']
        card_frame.buy_hide_btn = buy_widgets['hide_btn']
        card_frame.buy_note = buy_widgets['note']
        card_frame.sell_price = sell_widgets['price']
        card_frame.sell_change = sell_widgets['change']
        card_frame.sell_hide_btn = sell_widgets['hide_btn']
        card_frame.sell_note = sell_widgets['note']
        
        return card_frame
    
    def calculate_font_sizes(self, window_height):
        """윈도우 높이에 따른 폰트 크기 계산"""
        if window_height < 560:
            return 14, 12, 7
        elif window_height < 620:
            return 16, 14, 8
        elif window_height < 700:
            return 18, 16, 9
        else:
            return 20, 18, 10
    
    def on_window_resize(self, event):
        if event.widget == self.root:
            window_height = event.height
            
            if abs(window_height - self.current_window_height) > 30:
                self.current_window_height = window_height
                title_size, price_size, change_size = self.calculate_font_sizes(window_height)
                
                self.title_label.config(font=(self.FONT_FAMILY, title_size, 'bold'))
                
                for card in self.cards.values():
                    if hasattr(card, 'buy_price'):
                        card.buy_price.config(font=(self.FONT_FAMILY, price_size, 'bold'))
                        card.sell_price.config(font=(self.FONT_FAMILY, price_size, 'bold'))
                        card.buy_change.config(font=(self.FONT_FAMILY, change_size))
                        card.sell_change.config(font=(self.FONT_FAMILY, change_size))
    
    def scrape_gold_prices(self):
        try:
            url = "https://www.koreagoldx.co.kr/api/main"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            api_data = response.json()
            official = api_data['officialPrice4']
            
            data = {}
            for key, fields in self.API_FIELD_MAPPING.items():
                buy_price_field, buy_change_field, buy_diff_field, sell_price_field, sell_change_field, sell_diff_field = fields
                data[key] = {
                    'buy_price': f"{official[buy_price_field]:,}원",
                    'buy_change': f"{official[buy_change_field]}%",
                    'buy_diff': f"{official[buy_diff_field]:,}",
                    'sell_price': f"{official[sell_price_field]:,}원",
                    'sell_change': f"{official[sell_change_field]}%",
                    'sell_diff': f"{official[sell_diff_field]:,}"
                }
            
            # API 성공 - 마지막 성공 시간 업데이트
            self.last_success_time = time.time()
            self.last_update_datetime = datetime.now()  # 화면 표시용
            self.api_error = False
            
            return data
            
        except Exception as e:
            print(f"API 요청 오류: {e}")
            # 타임아웃 체크
            elapsed_minutes = (time.time() - self.last_success_time) / 60
            if elapsed_minutes >= self.error_timeout:
                self.api_error = True
            return None
    
    def extract_number(self, price_str):
        hide_text = self.custom_texts['hide_text']
        if not price_str or price_str == '-' or price_str == hide_text:
            return 0
        numbers = re.sub(r'[^\d]', '', price_str)
        return int(numbers) if numbers else 0
    
    def animate_price_change(self, label, old_value, new_value, steps=None, duration=None):
        if steps is None:
            steps = self.ANIMATION_STEPS
        if duration is None:
            duration = self.ANIMATION_DURATION
        old_num = self.extract_number(old_value)
        new_num = self.extract_number(new_value)
        
        hide_text = self.custom_texts['hide_text']
        if new_value == hide_text:
            label.config(text=new_value)
            return
        
        if old_num == new_num or old_num == 0:
            self.countup_animation(label, 0, new_num, steps, duration)
        else:
            self.countup_animation(label, old_num, new_num, steps, duration)
    
    def countup_animation(self, label, start, end, steps, total_duration):
        if steps <= 0:
            label.config(text=self.format_price(end))
            return
        
        current = start + (end - start) * (1 - steps / self.ANIMATION_STEPS)
        label.config(text=self.format_price(int(current)))
        
        delay = total_duration // self.ANIMATION_STEPS
        self.root.after(delay, lambda: self.countup_animation(label, start, end, steps - 1, total_duration))
    
    def format_price(self, price):
        if price == 0:
            return '-'
        return f"{price:,}원"
    
    def calculate_change_display(self, change_rate, diff):
        """변동률과 등락폭을 기반으로 색상, 화살표, 표시 텍스트 계산"""
        try:
            diff_num = int(diff.replace(',', ''))
            if diff_num < 0:
                color = self.COLOR_DOWN
                arrow = '▼'
                diff_display = f"{abs(diff_num):,}"
            else:
                color = self.COLOR_UP
                arrow = '▲'
                diff_display = f"{diff_num:,}"
        except:
            if '-' in str(change_rate):
                color = self.COLOR_DOWN
                arrow = '▼'
            else:
                color = self.COLOR_UP
                arrow = '▲'
            diff_display = diff
        return f"{change_rate} {arrow} {diff_display}", color
    
    def update_note(self, card, key, side):
        """노트 업데이트 (buy 또는 sell)"""
        if key not in self.NOTE_MAPPING:
            return
        
        note_attr = f'{side}_note'
        if not hasattr(card, note_attr):
            return
        
        note_key = self.NOTE_MAPPING[key][0 if side == 'buy' else 1]
        note_text = self.custom_texts[note_key]
        note_widget = getattr(card, note_attr)
        
        if note_text:
            note_widget.config(text=note_text)
            note_widget.pack(anchor='w', pady=(2, 0))
        else:
            note_widget.pack_forget()
    
    def update_price_side(self, card, key, side, item_data, old_price, is_hidden):
        """가격 측면(buy/sell) 업데이트"""
        hide_text = self.custom_texts['hide_text']
        price_attr = f'{side}_price'
        change_attr = f'{side}_change'
        hide_btn_attr = f'{side}_hide_btn'
        
        # Hide 버튼 텍스트 업데이트
        if hasattr(card, hide_btn_attr):
            getattr(card, hide_btn_attr).config(text="Show" if is_hidden else "Hide")
        
        if is_hidden:
            # 숨김 모드
            getattr(card, price_attr).config(text=hide_text, fg=self.COLOR_TEXT)
            getattr(card, change_attr).config(text="")
            if hasattr(card, f'{side}_note'):
                getattr(card, f'{side}_note').pack_forget()
        else:
            # 정상 표시
            price_text = item_data[f'{side}_price']
            getattr(card, price_attr).config(fg=self.COLOR_TEXT)
            self.animate_price_change(getattr(card, price_attr), old_price, price_text)
            
            # 변동률 표시
            change_rate = item_data[f'{side}_change']
            diff = item_data[f'{side}_diff']
            change_text, color = self.calculate_change_display(change_rate, diff)
            getattr(card, change_attr).config(text=change_text, fg=color)
            
            # 노트 표시
            self.update_note(card, key, side)
    
    def update_ui(self, data):
        # API 에러 상태 체크
        if self.api_error:
            error_msg = self.custom_texts['error_message']
            # 모든 카드에 에러 메시지 표시
            for card in self.cards.values():
                card.buy_price.config(text=error_msg, fg=self.COLOR_ERROR)
                card.buy_change.config(text="")
                card.sell_price.config(text=error_msg, fg=self.COLOR_ERROR)
                card.sell_change.config(text="")
            return
        
        if not data:
            return
        
        # 최신 데이터 저장
        self.latest_data = data
        
        # API 성공 시점의 시간을 표시 (시분초 포함)
        update_time = (self.last_update_datetime if hasattr(self, 'last_update_datetime') 
                      else datetime.now()).strftime("%Y.%m.%d %H:%M:%S")
        self.date_label.config(text=update_time)
        
        for key, card in self.cards.items():
            if key in data:
                item_data = data[key]
                old_data = self.previous_data.get(key, {})
                
                # buy/sell 각각 업데이트
                for side in ['buy', 'sell']:
                    is_hidden = key in self.hidden_items[side]
                    old_price = old_data.get(f'{side}_price', '')
                    self.update_price_side(card, key, side, item_data, old_price, is_hidden)
        
        self.previous_data = data.copy()
    
    def update_countdown(self):
        self.countdown_label.config(text=f"🔄 {self.countdown}")
    
    def auto_update_worker(self):
        while self.is_running:
            data = self.scrape_gold_prices()
            self.root.after(0, lambda d=data: self.update_ui(d))
            
            for i in range(self.update_interval, 0, -1):
                if not self.is_running:
                    break
                self.countdown = i
                self.root.after(0, self.update_countdown)
                time.sleep(1)
    
    def start_auto_update(self):
        data = self.scrape_gold_prices()
        self.update_ui(data)
        
        update_thread = threading.Thread(target=self.auto_update_worker, daemon=True)
        update_thread.start()
    
    def on_closing(self):
        self.is_running = False
        self.root.destroy()

def main():
    root = tk.Tk()
    app = GoldPriceApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
