from urllib.parse import urlencode
from django.http import HttpResponse
import requests
from django.conf import settings
from django.shortcuts import redirect
from django.shortcuts import render
from django.http import JsonResponse
from datetime import datetime, timedelta
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


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


'''
def get_event_json(request):
    """일정을 JSON 형태로 반환"""
    event_data = fetch_calendar_events()  # 구글 캘린더 API 호출 함수
    if "error" in event_data:
        return JsonResponse(event_data, status=400)

    # 응답 데이터
    response_data = {"alarms": event_data}

    return JsonResponse(response_data, content_type="application/json")
'''

def get_event_json(request):
    """Google Calendar API 데이터를 JSON 형태로 반환"""
    event_data = fetch_calendar_events()

    if "error" in event_data:
        response = JsonResponse(event_data, status=400)
    else:
        response = JsonResponse({"alarms": event_data}, content_type="application/json")

    # Access-Control-Allow-Origin 헤더 추가
    response["Access-Control-Allow-Origin"] = "*"
    return response

def parse_time_to_minutes(time_str):
    """HH:MM 형식의 문자열을 분 단위로 변환"""
    hours, minutes = map(int, time_str.split(":"))
    return hours * 60 + minutes



'''
@csrf_exempt
def set_alarm(request):
    """get_event_json 함수를 사용하여 일정 데이터를 기반으로 알람 생성"""
    if request.method == "POST":
        try:
            # 요청 데이터 파싱
            data = json.loads(request.body)
            prep_time = parse_time_to_minutes(data.get("prep_time"))  # 준비 시간 (분)
            alarm_interval = parse_time_to_minutes(data.get("alarm_interval"))  # 알람 주기 (분)
            wake_up_offset = parse_time_to_minutes(data.get("wake_up_offset"))  # 기상 시간 (분)
            departure_offset = parse_time_to_minutes(data.get("departure_offset"))  # 출발 시간 (분)

            # 같은 파일 내의 get_event_json 함수 호출
            events_response = get_event_json(request)

            # JsonResponse 객체를 JSON으로 변환
            if events_response.status_code != 200:
                return events_response  # 오류가 있는 경우 그대로 반환
            events_data = json.loads(events_response.content)

            events = events_data.get("alarms", [])
            if not events:
                return JsonResponse({"message": "No events found in the calendar"}, status=200)

            alarms_by_event = []  # 각 일정에 대한 알람 저장

            for event in events:
                # 일정 시작 시간 파싱
                title = event.get("title", "No Title")
                date_str = event.get("date")
                time_str = event.get("time")
                if not date_str or not time_str:
                    continue

                # 날짜와 시간 결합하여 datetime 객체 생성
                event_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")

                # 기상 시간 및 출발 시간 계산
                wake_up_time = event_time - timedelta(minutes=wake_up_offset)
                departure_time = event_time - timedelta(minutes=departure_offset)

                # 알람 생성
                alarms = []

                # 기상 시간에 따른 알람 생성
                current_time = wake_up_time - timedelta(minutes=prep_time)
                while current_time < wake_up_time:
                    alarms.append(current_time.strftime("%H:%M"))
                    current_time += timedelta(minutes=alarm_interval)
                current_time = wake_up_time
                while current_time < departure_time:
                    alarms.append(current_time.strftime("%H:%M"))
                    current_time += timedelta(minutes=alarm_interval)

                # 출발 시간에 따른 알람 생성
                current_time = departure_time - timedelta(minutes=prep_time)
                while current_time < departure_time:
                    alarms.append(current_time.strftime("%H:%M"))
                    current_time += timedelta(minutes=alarm_interval)
                current_time = departure_time
                while current_time < event_time:
                    alarms.append(current_time.strftime("%H:%M"))
                    current_time += timedelta(minutes=alarm_interval)

                # 일정별 결과 저장
                alarms_by_event.append({
                    "title": title,
                    "event_time": event_time.strftime("%Y-%m-%d %H:%M"),
                    "alarms": alarms
                })

            return JsonResponse({"alarms_by_event": alarms_by_event, "message": "Alarm schedules created successfully!"})

        except (ValueError, KeyError) as e:
            return JsonResponse({"error": f"Invalid data: {str(e)}"}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=405)'''


@csrf_exempt
def set_alarm(request):
    """일정 데이터를 기반으로 알람 생성"""
    if request.method == "POST":
        try:
            # 요청 데이터 파싱
            data = json.loads(request.body)
            prep_time = parse_time_to_minutes(data.get("prep_time"))  # 준비 시간 (분)
            alarm_interval = parse_time_to_minutes(data.get("alarm_interval"))  # 알람 주기 (분)
            wake_up_offset = parse_time_to_minutes(data.get("wake_up_offset"))  # 기상 시간 (분)
            departure_offset = parse_time_to_minutes(data.get("departure_offset"))  # 출발 시간 (분)

            # 같은 파일 내의 get_event_json 함수 호출
            events_response = get_event_json(request)

            # JsonResponse 객체를 JSON으로 변환
            if events_response.status_code != 200:
                return events_response  # 오류가 있는 경우 그대로 반환
            events_data = json.loads(events_response.content)

            events = events_data.get("alarms", [])
            if not events:
                return JsonResponse({"message": "No events found in the calendar"}, status=200)

            alarms_by_event = []  # 각 일정에 대한 알람 저장

            for event in events:
                # 일정 시작 시간 파싱
                title = event.get("title", "No Title")
                date_str = event.get("date")
                time_str = event.get("time")
                if not date_str or not time_str:
                    continue

                # 날짜와 시간 결합하여 datetime 객체 생성
                event_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")

                # 기상 시간 및 출발 시간 계산
                wake_up_time = event_time - timedelta(minutes=wake_up_offset)
                departure_time = event_time - timedelta(minutes=departure_offset)

                # 알람 생성
                alarms = []

                # 기상 시간 알람 생성 (앞으로 4개, 뒤로 2개)
                for i in range(3, 0, -1):
                    alarm_time = wake_up_time - timedelta(minutes=i * alarm_interval)
                    if alarm_time.time() < wake_up_time.time():
                        alarms.append(alarm_time.strftime("%H:%M"))
                alarms.append(wake_up_time.strftime("%H:%M"))
                for i in range(1, 3):  # 고정된 2개
                    alarm_time = wake_up_time + timedelta(minutes=i * alarm_interval)
                    if alarm_time.time() > wake_up_time.time():
                        alarms.append(alarm_time.strftime("%H:%M"))

                # 출발 시간 알람 생성 (앞으로 4개, 뒤로 2개)
                for i in range(3, 0, -1):
                    alarm_time = departure_time - timedelta(minutes=i * alarm_interval)
                    if alarm_time.time() < departure_time.time():
                        alarms.append(alarm_time.strftime("%H:%M"))
                alarms.append(departure_time.strftime("%H:%M"))
                for i in range(1, 3):  # 고정된 2개
                    alarm_time = departure_time + timedelta(minutes=i * alarm_interval)
                    if alarm_time.time() > departure_time.time():
                        alarms.append(alarm_time.strftime("%H:%M"))

                # 중복 제거 및 정렬
                alarms = sorted(set(alarms))
                alarms_by_event.append({
                    "title": title,
                    "event_time": event_time.strftime("%Y-%m-%d %H:%M"),
                    "alarms": alarms
                })

            return JsonResponse({"alarms_by_event": alarms_by_event, "message": "Alarm schedules created successfully!"})

        except (ValueError, KeyError) as e:
            return JsonResponse({"error": f"Invalid data: {str(e)}"}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=405)


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
