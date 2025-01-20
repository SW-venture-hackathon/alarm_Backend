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

calendar_id = "e0fe6e867084ce29a8d5e4a9f76ce6c6207b6ff0b6d7cbd69f6bd937174dbbc6@group.calendar.google.com"
api_key = "AIzaSyBmgTKsv5vApLr8q-i0JA-iQOAira-V_MU"

def main(request):
    return render(request, 'main.html')


def fetch_calendar_events():
    # """Google Calendar API에서 일정 데이터를 가져오는 함수"""
    # calendar_id = "your-calendar-id@group.calendar.google.com"
    # api_key = "your-api-key"
    url = f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events?key={api_key}"

    response = requests.get(url)
    if response.status_code != 200:
        return {"error": "Failed to fetch calendar events"}

    events = response.json().get("items", [])
    processed_events = []

    for event in events:
        # 시작 시간 처리
        start = event.get("start", {}).get("dateTime") or event.get("start", {}).get("date")

        # 날짜 및 시간 분리
        if start:
            start_date, start_time = start.split("T") if "T" in start else (start, None)
        else:
            start_date, start_time = None, None

        if start_time:
            start_time = ":".join(start_time.split(":")[:2])

        processed_events.append({
            "title": event.get("summary", "No Title"),
            "date": start_date,
            "time": start_time.split("+")[0] if start_time else None,
        })

    return processed_events


def public_calendar_view(request):
    """캘린더 데이터를 HTML로 렌더링"""
    alarm_data = fetch_calendar_events()
    if "error" in alarm_data:
        return JsonResponse(alarm_data, status=400)

    return render(request, "calendar_list.html", {"alarms": alarm_data})


def get_alarms_json(request):
    """일정을 JSON 형태로 반환"""
    alarm_data = fetch_calendar_events()
    if "error" in alarm_data:
        return JsonResponse(alarm_data, status=400)

    return JsonResponse({"alarms": alarm_data})


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
