import requests
import os
import subprocess
import time
from icalendar import Calendar
from datetime import datetime, date, timedelta

# --- [설정 세션] ---
GITHUB_ID = "ara-house"  
REPO_NAME = "ara-house"

# 2026년 주요 공휴일 리스트 (직접 관리)
MANUAL_HOLIDAYS = [
    date(2026, 1, 1),   # 신정
    date(2026, 2, 16),  # 설날 연휴
    date(2026, 2, 17),
    date(2026, 2, 18),
    date(2026, 3, 1),   # 삼일절
    date(2026, 3, 2),   # (대체공휴일)
    date(2026, 5, 5),   # 어린이날
    date(2026, 5, 24),  # 부처님 오신 날
    date(2026, 5, 25),  # (대체공휴일)
    date(2026, 6, 6),   # 현충일
    date(2026, 8, 15),  # 광복절
    date(2026, 9, 24),  # 추석 연휴
    date(2026, 9, 25),
    date(2026, 9, 26),
    date(2026, 10, 3),  # 개천절
    date(2026, 10, 9),  # 한글날
    date(2026, 12, 25), # 성탄절
]

ROOMS = {
    "101": ["https://www.airbnb.com/calendar/ical/943393120131594100.ics?t=690b082ab1ba452ebf05c17aa9dd756c&locale=ko", "https://ical.booking.com/v1/export?t=ab8f4840-c4f2-43ef-a81b-3c3b6f6b9747"],
    "102": ["https://www.airbnb.com/calendar/ical/40381467.ics?t=5845a99e7f93423e8b01ce19d756d77a&locale=ko", "https://ical.booking.com/v1/export?t=10d52aec-4995-4cf7-aa69-0bc6ff8bc956"],
    "201": ["https://www.airbnb.com/calendar/ical/996755620088734555.ics?t=00a1bea2a48149988dff72f9e85b3795&locale=ko", "https://ical.booking.com/v1/export?t=47707b9a-a955-4ddc-8220-d5203346914d"],
    "203": ["https://www.airbnb.com/calendar/ical/992456128728771332.ics?t=b9a5bc5c35ca49d8b9b80c8cc4be4fe7&locale=ko", "https://ical.booking.com/v1/export?t=81a8f4fb-9f4c-435d-80f4-f55abdab19ec"],
    "205": ["https://www.airbnb.com/calendar/ical/951839531665472879.ics?t=9351bffa88a04a60ac8a8e7832b4a712&locale=ko", "https://ical.booking.com/v1/export?t=08c0af99-26f4-49bf-9296-5bfac2060ab4"],
    "207": ["https://www.airbnb.com/calendar/ical/946046066669091848.ics?t=5ebb910321f049c5a0ecb1cce8e29a76&locale=ko", "https://ical.booking.com/v1/export?t=9e14c27b-c126-4f7a-81d2-3ab6860427c9"],
    "209": ["https://www.airbnb.com/calendar/ical/948965969214960122.ics?t=b9c79d14ad844848afdce207bbdc84f2&locale=ko", "https://ical.booking.com/v1/export?t=9c3e31c4-2966-42ba-8210-6e6f0eda9b36"],
    "301": ["https://www.airbnb.com/calendar/ical/959116652669574749.ics?t=9e14191aad504e25b65a6895f4bcfc53&locale=ko", "https://ical.booking.com/v1/export/t/64c16c6f-8e30-41a2-bc14-47031c8c44ee.ics", "https://ebooking.ctrip.com/ebkovsroom/icalendar/export/0bb518ed-7610-4d74-b2af-76b9266c0efb.ics"],
    "303": ["https://www.airbnb.com/calendar/ical/945930870271086972.ics?t=39e9009785e64eb2941d28268fb01cc9&locale=ko", "https://ical.booking.com/v1/export?t=0a62d6ca-c696-4475-96e5-8072750595f8"],
    "305": ["https://www.airbnb.com/calendar/ical/967890654459653203.ics?t=3dcb8fa649fb4b369aaec4de575ded03&locale=ko", "https://ical.booking.com/v1/export?t=11139a6c-c6fa-4b9c-a3dc-69cef4d283cb"],
    "307": ["https://www.airbnb.com/calendar/ical/989587973362444490.ics?t=11dde13626cc4ee686fccf7d986f2498&locale=ko", "https://ical.booking.com/v1/export?t=cc0686b8-a6ed-45ad-8407-0036fd379394"],
    "309": ["https://www.airbnb.com/calendar/ical/944552717786766263.ics?t=41a94c9cc8034397a51fdcd8f445f2f5&locale=ko", "https://ical.booking.com/v1/export?t=173bb36e-c6a4-431d-abd2-f4b28f39b771"],
}

def run_git_commands():
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(current_dir)
        subprocess.run(["git", "add", "index.html"], check=True)
        commit_msg = f"Auto update: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True, capture_output=True)
        subprocess.run(["git", "push", "origin", "main"], check=True, capture_output=True)
        print(f"✅ GitHub 업데이트 완료!", flush=True)
    except Exception as e:
        print(f"❌ Git 오류: {e}", flush=True)

def generate_dashboard(rooms_dict, days=31):
    today = date.today()
    tomorrow = today + timedelta(days=1)
    date_list = [today + timedelta(days=i) for i in range(days)]
    checkouts_today, checkouts_tomorrow, checkins_today = [], [], []
    overbooked_alert, room_results = set(), {}

    print(f"📦 데이터 수집 중...", flush=True)

    for room, urls in rooms_dict.items():
        day_map = {}
        for url in urls:
            if not url: continue
            try:
                res = requests.get(url, timeout=7)
                cal = Calendar.from_ical(res.content)
                
                # 👇 트립닷컴 도메인 인식 로직 추가 (trip.com 또는 ctrip.com)
                is_booking = "booking.com" in url.lower()
                is_airbnb = "airbnb.com" in url.lower()
                is_trip = "trip.com" in url.lower() or "ctrip.com" in url.lower() 
                
                for event in cal.walk('VEVENT'):
                    s, e = event.get('dtstart').dt, event.get('dtend').dt
                    summary = str(event.get('summary', '')).lower()
                    if isinstance(s, datetime): s, e = s.date(), e.date()
                    
                    # 👇 트립닷컴 우선순위 및 타입 할당
                    if is_booking: p_type, priority = "booking", 3
                    elif is_trip: p_type, priority = "trip", 4 
                    elif is_airbnb:
                        if "unavailable" in summary or "not available" in summary: p_type, priority = "manual", 1
                        else: p_type, priority = "airbnb", 2
                    else: p_type, priority = "manual", 1
                    
                    curr = s
                    while curr < e:
                        if curr in day_map:
                            if day_map[curr]['priority'] >= 2 and priority >= 2 and day_map[curr]['type'] != p_type:
                                day_map[curr] = {'type': 'overbooked', 'priority': 99}; overbooked_alert.add(room)
                            elif day_map[curr]['priority'] < priority: day_map[curr] = {'type': p_type, 'priority': priority}
                        else: day_map[curr] = {'type': p_type, 'priority': priority}
                        curr += timedelta(days=1)
                    
                    if e == today: checkouts_today.append(room)
                    if e == tomorrow: checkouts_tomorrow.append(room)
                    if s == today: checkins_today.append(room)
            except: continue
        room_results[room] = day_map

    def get_chips(room_list):
        if not room_list: return "-"
        return "".join([f'<span class="room-chip">{r}</span>' for r in sorted(set(room_list))])

    # 👇 CSS에 트립닷컴 색상(--trip) 및 클래스(.booked-trip) 반영
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>아라 하우스 통합 관리</title>
        <style>
            :root {{ --airbnb: #FF385C; --booking: #003580; --trip: #3264ff; --manual: #748ffc; --overbooked: #212529; --bg: #f8f9fa; --sun: #fff5f5; --sat: #f0f7ff; }}
            body {{ font-family: 'Pretendard', sans-serif; background: var(--bg); margin: 0; padding: 15px; color: #333; }}
            .header {{ display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 20px; }}
            .alert-bar {{ background: #fff5f5; border: 2px solid #ff6b6b; color: #fa5252; padding: 12px; border-radius: 12px; margin-bottom: 15px; font-weight: bold; text-align: center; animation: blink 1.5s infinite; }}
            @keyframes blink {{ 0% {{ opacity: 1; }} 50% {{ opacity: 0.6; }} 100% {{ opacity: 1; }} }}
            .summary-container {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; margin-bottom: 20px; }}
            .card {{ background: white; padding: 12px 5px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border-top: 4px solid #ddd; text-align: center; }}
            .card h3 {{ margin: 0 0 8px 0; font-size: 10px; color: #888; }}
            .card .list {{ display: flex; flex-wrap: wrap; gap: 4px; justify-content: center; }}
            .room-chip {{ background: #f1f3f5; padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: bold; color: #495057; }}
            .checkout {{ border-top-color: #ffa94d; }} 
            .tmr-checkout {{ border-top-color: #fab005; background: #fffdf2; }} 
            .checkin {{ border-top-color: #63e6be; }}
            .container {{ background: white; padding: 15px; border-radius: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); overflow-x: auto; }}
            table {{ border-collapse: collapse; width: 100%; min-width: 900px; table-layout: fixed; }}
            th, td {{ border: 1px solid #f1f3f5; padding: 10px 0; text-align: center; font-size: 12px; }}
            th {{ background: #f8f9fa; position: sticky; top: 0; z-index: 5; }}
            .room-name {{ background: white; font-weight: bold; position: sticky; left: 0; z-index: 10; border-right: 3px solid #eee; width: 55px; }}
            .is-holiday, .is-sunday {{ background: var(--sun) !important; color: #e03131; }}
            .is-saturday {{ background: var(--sat) !important; color: #1971c2; }}
            .is-today {{ background: #fff9db !important; border: 2px solid #fab005 !important; }}
            .booked-airbnb {{ background: var(--airbnb) !important; }}
            .booked-booking {{ background: var(--booking) !important; }}
            .booked-trip {{ background: var(--trip) !important; }}
            .booked-manual {{ background: var(--manual) !important; }}
            .booked-overbooked {{ background: var(--overbooked) !important; background-image: repeating-linear-gradient(45deg, transparent, transparent 5px, #fcc419 5px, #fcc419 10px) !important; }}
        </style>
    </head>
    <body>
        <div class="header"><h1>🐾 ARA HOUSE</h1><div style="text-align:right;"><div style="font-weight:bold; font-size:16px;">{today.strftime('%m/%d')}</div><div style="font-size:10px; color:#999;">{datetime.now().strftime('%H:%M')} UP</div></div></div>
        {f'<div class="alert-bar">⚠️ 긴급: {", ".join(sorted(overbooked_alert))}호 중복 예약!</div>' if overbooked_alert else ''}
        <div class="summary-container">
            <div class="card checkout"><h3>🧹 오늘 퇴실</h3><div class="list">{get_chips(checkouts_today)}</div></div>
            <div class="card tmr-checkout"><h3>📅 내일 퇴실</h3><div class="list">{get_chips(checkouts_tomorrow)}</div></div>
            <div class="card checkin"><h3>🔑 오늘 입실</h3><div class="list">{get_chips(checkins_today)}</div></div>
        </div>
        <div class="container"><table><thead><tr><th class="room-name">객실</th>{''.join(f'''<th class="{'is-today' if d == today else ('is-holiday' if d in MANUAL_HOLIDAYS or d.weekday() == 6 else ('is-saturday' if d.weekday() == 5 else ''))}">{d.day}<br><small>{d.month}월</small></th>''' for d in date_list)}</tr></thead><tbody>
    """

    for room, day_map in room_results.items():
        html_content += f'<tr><td class="room-name">{room}</td>'
        for d in date_list:
            day_class = "is-today" if d == today else ("is-holiday" if d in MANUAL_HOLIDAYS or d.weekday() == 6 else ("is-saturday" if d.weekday() == 5 else ""))
            status_class = f"booked-{day_map[d]['type']}" if d in day_map else ""
            html_content += f'<td class="{status_class} {day_class}"></td>'
        html_content += "</tr>"

    html_content += "</tbody></table></div></body></html>"
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, "index.html")
    with open(file_path, "w", encoding="utf-8") as f: f.write(html_content)
    run_git_commands()

if __name__ == "__main__":
    print(f"🚀 [{datetime.now().strftime('%H:%M:%S')}] 업데이트 시작!", flush=True)
    try:
        generate_dashboard(ROOMS)
        print(f"✨ 모든 작업이 완료되었습니다.", flush=True)
    except Exception as e:
        print(f"❌ 오류 발생: {e}", flush=True)