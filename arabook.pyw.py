import requests
import os
import webbrowser
import holidays
import subprocess
from icalendar import Calendar
from datetime import datetime, date, timedelta

# --- [설정 세션: 본인의 정보에 맞게 확인해 주세요] ---
GITHUB_ID = "ara-house" 
REPO_NAME = "ara-house"
# ----------------------------------------------

# 한국 공휴일 설정
kr_holidays = holidays.KR()

# 1. 12개 객실 주소 관리 (모든 주소 반영 완료)
ROOMS = {
    "101": [
        "https://www.airbnb.com/calendar/ical/943393120131594100.ics?t=690b082ab1ba452ebf05c17aa9dd756c&locale=ko",
        "https://ical.booking.com/v1/export?t=ab8f4840-c4f2-43ef-a81b-3c3b6f6b9747"
    ],
    "102": [
        "https://www.airbnb.com/calendar/ical/40381467.ics?t=5845a99e7f93423e8b01ce19d756d77a&locale=ko",
        "https://ical.booking.com/v1/export?t=10d52aec-4995-4cf7-aa69-0bc6ff8bc956"
    ],
    "201": [
        "https://www.airbnb.com/calendar/ical/996755620088734555.ics?t=00a1bea2a48149988dff72f9e85b3795&locale=ko",
        "https://ical.booking.com/v1/export?t=47707b9a-a955-4ddc-8220-d5203346914d"
    ],
    "203": [
        "https://www.airbnb.com/calendar/ical/992456128728771332.ics?t=b9a5bc5c35ca49d8b9b80c8cc4be4fe7&locale=ko",
        "https://ical.booking.com/v1/export?t=81a8f4fb-9f4c-435d-80f4-f55abdab19ec"
    ],
    "205": [
        "https://www.airbnb.com/calendar/ical/951839531665472879.ics?t=9351bffa88a04a60ac8a8e7832b4a712&locale=ko",
        "https://ical.booking.com/v1/export?t=08c0af99-26f4-49bf-9296-5bfac2060ab4"
    ], 
    "207": [
        "https://www.airbnb.com/calendar/ical/946046066669091848.ics?t=5ebb910321f049c5a0ecb1cce8e29a76&locale=ko",
        "https://ical.booking.com/v1/export?t=9e14c27b-c126-4f7a-81d2-3ab6860427c9"
    ], 
    "209": [
        "https://www.airbnb.com/calendar/ical/948965969214960122.ics?t=b9c79d14ad844848afdce207bbdc84f2&locale=ko",
        "https://ical.booking.com/v1/export?t=9c3e31c4-2966-42ba-8210-6e6f0eda9b36"
    ],
    "301": [
        "https://www.airbnb.com/calendar/ical/959116652669574749.ics?t=9e14191aad504e25b65a6895f4bcfc53&locale=ko",
        "https://ical.booking.com/v1/export?t=285a62f6-24c5-4f48-8ad7-2b9d5b09b065"
    ], 
    "303": [
        "https://www.airbnb.com/calendar/ical/945930870271086972.ics?t=39e9009785e64eb2941d28268fb01cc9&locale=ko",
        "https://ical.booking.com/v1/export?t=0a62d6ca-c696-4475-96e5-8072750595f8"
    ],
    "305": [
        "https://www.airbnb.com/calendar/ical/967890654459653203.ics?t=3dcb8fa649fb4b369aaec4de575ded03&locale=ko",
        "https://ical.booking.com/v1/export?t=11139a6c-c6fa-4b9c-a3dc-69cef4d283cb"
    ], 
    "307": [
        "https://www.airbnb.com/calendar/ical/989587973362444490.ics?t=11dde13626cc4ee686fccf7d986f2498&locale=ko",
        "https://ical.booking.com/v1/export?t=cc0686b8-a6ed-45ad-8407-0036fd379394"
    ], 
    "309": [
        "https://www.airbnb.com/calendar/ical/944552717786766263.ics?t=41a94c9cc8034397a51fdcd8f445f2f5&locale=ko",
        "https://ical.booking.com/v1/export?t=173bb36e-c6a4-431d-abd2-f4b28f39b771"
    ],
}

def run_git_commands():
    """작성된 index.html을 GitHub로 전송"""
    try:
        # 작업 디렉토리를 코드가 있는 폴더로 확실히 고정
        current_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(current_dir)
        
        subprocess.run(["git", "add", "index.html"], check=True)
        commit_msg = f"Auto update: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        print(f"✅ {datetime.now().strftime('%H:%M')} - GitHub 업데이트 성공!")
    except Exception as e:
        print(f"❌ GitHub 업데이트 중 오류: {e}")

def generate_dashboard(rooms_dict, days=31):
    today = date.today()
    date_list = [today + timedelta(days=i) for i in range(days)]
    
    checkouts_today = []
    checkins_today = []
    overbooked_alert = set()
    room_results = {}

    for room, urls in rooms_dict.items():
        day_map = {} 
        for url in urls:
            if not url: continue
            try:
                res = requests.get(url, timeout=7)
                cal = Calendar.from_ical(res.content)
                is_booking_source = "booking.com" in url.lower()
                is_airbnb_source = "airbnb.com" in url.lower()
                
                for event in cal.walk('VEVENT'):
                    s, e = event.get('dtstart').dt, event.get('dtend').dt
                    summary = str(event.get('summary', '')).lower()
                    if isinstance(s, datetime): s, e = s.date(), e.date()
                    
                    if is_booking_source: p_type, priority = "booking", 3
                    elif is_airbnb_source:
                        if "unavailable" in summary or "not available" in summary:
                            p_type, priority = "manual", 1
                        else: p_type, priority = "airbnb", 2
                    else: p_type, priority = "manual", 1

                    curr = s
                    while curr < e:
                        if curr in day_map:
                            existing = day_map[curr]
                            if existing['priority'] >= 2 and priority >= 2 and existing['type'] != p_type:
                                day_map[curr] = {'type': 'overbooked', 'priority': 99}
                                overbooked_alert.add(room)
                            elif existing['priority'] < priority:
                                day_map[curr] = {'type': p_type, 'priority': priority}
                        else:
                            day_map[curr] = {'type': p_type, 'priority': priority}
                        curr += timedelta(days=1)
                    
                    if e == today: checkouts_today.append(room)
                    if s == today: checkins_today.append(room)
            except: continue
        room_results[room] = day_map

    # HTML 생성 시작 (index.html로 변경 및 모바일 대응 Meta 태그 추가)
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta http-equiv="refresh" content="3600">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>아라 하우스 통합 관리 시스템</title>
        <style>
            :root {{ 
                --airbnb: #FF385C; --booking: #003580; --manual: #748ffc; 
                --overbooked: #212529; --bg: #f8f9fa;
                --sun: #fff5f5; --sat: #f0f7ff;
            }}
            body {{ font-family: 'Pretendard', sans-serif; background: var(--bg); margin: 0; padding: 15px; color: #333; }}
            .header {{ display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 20px; }}
            h1 {{ font-size: 22px; margin: 0; }}
            
            .alert-bar {{ 
                background: #fff5f5; border: 2px solid #ff6b6b; color: #fa5252; padding: 12px; 
                border-radius: 12px; margin-bottom: 20px; font-weight: bold; font-size: 14px;
                animation: blink 1.5s infinite; text-align: center;
            }}
            @keyframes blink {{ 0% {{ opacity: 1; }} 50% {{ opacity: 0.6; }} 100% {{ opacity: 1; }} }}

            .summary-container {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 20px; }}
            .card {{ background: white; padding: 15px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border-left: 5px solid #ddd; }}
            .card h3 {{ margin: 0 0 5px 0; font-size: 11px; color: #888; }}
            .card .list {{ font-size: 16px; font-weight: bold; }}
            .checkout {{ border-left-color: #ffa94d; }}
            .checkin {{ border-left-color: #63e6be; }}

            .container {{ background: white; padding: 15px; border-radius: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); overflow-x: auto; }}
            table {{ border-collapse: collapse; width: 100%; min-width: 1000px; table-layout: fixed; }}
            th, td {{ border: 1px solid #f1f3f5; padding: 10px 0; text-align: center; font-size: 12px; }}
            th {{ background: #f8f9fa; position: sticky; top: 0; z-index: 5; height: 40px; }}
            .room-name {{ background: white; font-weight: bold; position: sticky; left: 0; z-index: 10; border-right: 3px solid #eee; width: 55px; }}
            
            .is-holiday, .is-sunday {{ background: var(--sun) !important; color: #e03131; }}
            .is-saturday {{ background: var(--sat) !important; color: #1971c2; }}
            .is-today {{ background: #fff9db !important; border: 2px solid #fab005 !important; font-weight: bold; }}
            
            .booked-airbnb {{ background: var(--airbnb) !important; }}
            .booked-booking {{ background: var(--booking) !important; }}
            .booked-manual {{ background: var(--manual) !important; }}
            .booked-overbooked {{ 
                background: var(--overbooked) !important; 
                background-image: repeating-linear-gradient(45deg, transparent, transparent 5px, #fcc419 5px, #fcc419 10px) !important;
            }}
            
            .legend {{ margin-top: 20px; display: flex; flex-wrap: wrap; gap: 10px; justify-content: flex-start; font-size: 11px; }}
            .dot {{ width: 10px; height: 10px; border-radius: 2px; display: inline-block; margin-right: 4px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🐾 ARA HOUSE</h1>
            <div style="text-align:right;">
                <div style="font-weight:bold; font-size:16px;">{today.strftime('%m/%d')}</div>
                <div style="font-size:10px; color:#999;">UPDATE: {datetime.now().strftime('%H:%M')}</div>
            </div>
        </div>

        {f'<div class="alert-bar">⚠️ 긴급: {", ".join(sorted(overbooked_alert))}호 오버부킹 확인 필요!</div>' if overbooked_alert else ''}

        <div class="summary-container">
            <div class="card checkout"><h3>🧹 OUT (청소)</h3><div class="list">{", ".join(sorted(set(checkouts_today))) if checkouts_today else "-"}</div></div>
            <div class="card checkin"><h3>🔑 IN (입실)</h3><div class="list">{", ".join(sorted(set(checkins_today))) if checkins_today else "-"}</div></div>
        </div>

        <div class="container">
            <table>
                <thead>
                    <tr>
                        <th class="room-name">객실</th>
                        {''.join(f'''<th class="{'is-today' if d == today else ('is-holiday' if d in kr_holidays or d.weekday() == 6 else ('is-saturday' if d.weekday() == 5 else ''))}">{d.day}<br><small>{d.month}월</small>{f'<div style="font-size:8px; font-weight:normal;">{kr_holidays.get(d)[:2]}</div>' if d in kr_holidays else ''}</th>''' for d in date_list)}
                    </tr>
                </thead>
                <tbody>
    """

    for room, day_map in room_results.items():
        html_content += f'<tr><td class="room-name">{room}</td>'
        for d in date_list:
            day_class = "is-holiday" if d in kr_holidays or d.weekday() == 6 else ("is-saturday" if d.weekday() == 5 else "")
            if d == today: day_class = "is-today"
            status_class = f"booked-{day_map[d]['type']}" if d in day_map else ""
            html_content += f'<td class="{status_class} {day_class}"></td>'
        html_content += "</tr>"

    html_content += f"""
                </tbody>
            </table>
        </div>
        <div class="legend">
            <div><span class="dot" style="background:var(--airbnb)"></span>Air</div>
            <div><span class="dot" style="background:var(--booking)"></span>Book</div>
            <div><span class="dot" style="background:var(--manual)"></span>직접</div>
            <div><span class="dot" style="background:var(--overbooked); background-image: repeating-linear-gradient(45deg, transparent, transparent 2px, #fcc419 2px, #fcc419 4px);"></span>중복</div>
        </div>
    </body>
    </html>
    """
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # GitHub Pages는 index.html을 첫 화면으로 인식하므로 이름을 바꿉니다.
    file_path = os.path.join(current_dir, "index.html")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    # Git 전송 실행
    run_git_commands()

if __name__ == "__main__":
    generate_dashboard(ROOMS)