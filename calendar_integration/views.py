from urllib.parse import urlencode
from django.http import HttpResponse
import requests
from django.conf import settings
from django.shortcuts import redirect
from django.shortcuts import render
from django.http import JsonResponse
from datetime import datetime, timedelta


# Mocked events (캘린더 API로 받아오는 데이터 대신 임시 데이터로 테스트)
mocked_events = [
    {
        "summary": "Meeting with Team",
        "start": {"dateTime": "2025-01-21T10:00:00"},
    },
    {
        "summary": "Doctor Appointment",
        "start": {"dateTime": "2025-01-22T15:30:00"},
    },
]


def main(request):
    return render(request, 'main.html')


def public_calendar_view(request):
    """공유 캘린더에서 이벤트 데이터 가져오기"""
    calendar_id = "e0fe6e867084ce29a8d5e4a9f76ce6c6207b6ff0b6d7cbd69f6bd937174dbbc6@group.calendar.google.com"
    api_key = "AIzaSyBmgTKsv5vApLr8q-i0JA-iQOAira-V_MU"  # Google API 키
    url = f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events?key={api_key}"

    response = requests.get(url)
    if response.status_code != 200:
        return JsonResponse({"error": "Failed to fetch calendar events"}, status=400)

    # 이벤트 데이터
    events = response.json().get("items", [])
    return render(request, "calendar_list.html", {"events": events})


def google_login(request):
    base_url = "https://accounts.google.com/o/oauth2/auth"
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "https://www.googleapis.com/auth/calendar.readonly",
        "access_type": "offline",
        "prompt": "consent",
    }
    login_url = f"{base_url}?{urlencode(params)}"
    return redirect(login_url)


def google_redirect(request):
    code = request.GET.get("code")
    if not code:
        return JsonResponse({"error": "Authorization code missing"}, status=400)

    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }

    response = requests.post(token_url, data=data)
    if response.status_code != 200:
        return JsonResponse({"error": "Failed to fetch token"}, status=400)

    token_info = response.json()
    request.session['credentials'] = token_info
    return redirect('calendar')


'''
def calendar_view(request):
    """Google Calendar API를 사용하여 일정 가져오고 알람 생성"""
    # 1. 사용자 인증 정보 확인
    credentials = request.session.get('credentials')
    if not credentials:
        return redirect('main')  # 인증되지 않은 경우 메인 화면으로 이동

    # 2. Google Calendar API 호출
    access_token = credentials.get('access_token')
    headers = {"Authorization": f"Bearer {access_token}"}
    events_url = "https://www.googleapis.com/calendar/v3/calendars/primary/events"
    response = requests.get(events_url, headers=headers)
    if response.status_code != 200:
        return JsonResponse({"error": "Failed to fetch events", "details": response.json()}, status=400)

    # 3. 이벤트 데이터 가져오기 및 정렬
    events = response.json().get('items', [])
    events = sorted(events, key=lambda x: x.get('start', {}).get('dateTime', x.get('start', {}).get('date', '')))

    # 4. 알람 생성 파라미터 설정 (임의의 값)
    preparation_time = timedelta(minutes=60)  # 준비 시간: 1시간
    start_offset = timedelta(minutes=120)    # 알람 시작 시간: 2시간 전
    alarm_interval = timedelta(minutes=5)    # 알람 주기: 5분

    # 5. 알람 생성
    all_alarms = []
    for event in events:
        # 시작 시간 가져오기
        start_time_str = event.get('start', {}).get('dateTime')  # ISO 형식
        if not start_time_str:
            continue  # 시작 시간이 없으면 건너뜀

        # 시작 시간을 datetime 객체로 변환
        schedule_time = datetime.fromisoformat(start_time_str)

        # 알람 시작 및 종료 시간 계산
        alarm_start_time = schedule_time - preparation_time - start_offset
        alarm_end_time = schedule_time - preparation_time

        # 알람 시간 계산 (5분 간격)
        alarms = []
        current_time = alarm_start_time
        while current_time <= alarm_end_time:
            alarms.append(current_time.strftime('%Y-%m-%d %H:%M:%S'))
            current_time += alarm_interval

        # 알람 데이터 추가
        all_alarms.append({
            "event": event.get('summary', 'No Title'),  # 이벤트 제목
            "alarms": alarms,
        })

    # 6. 결과 반환
    return render(request, 'calendar.html', {"alarms": all_alarms})


'''
def calendar_view(request):
    """Google Calendar API를 사용하여 일정 가져오기"""
    credentials = request.session.get('credentials')
    if not credentials:
        return redirect('main')  # 인증되지 않은 경우 메인 화면으로 이동

    access_token = credentials.get('access_token')
    headers = {"Authorization": f"Bearer {access_token}"}
    events_url = "https://www.googleapis.com/calendar/v3/calendars/primary/events"

    response = requests.get(events_url, headers=headers)
    if response.status_code != 200:
        return JsonResponse({"error": "Failed to fetch events", "details": response.json()}, status=400)

    # API에서 가져온 이벤트 데이터
    events = response.json().get('items', [])

    # 이벤트 데이터를 정렬 (시작 시간 기준)
    events = sorted(events, key=lambda x: x.get('start', {}).get('dateTime', x.get('start', {}).get('date', '')))

    return render(request, 'calendar.html', {"events": events})
