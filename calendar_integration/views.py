from urllib.parse import urlencode
from django.http import HttpResponse
import requests
from django.conf import settings
from django.shortcuts import redirect
from django.shortcuts import render
from django.http import JsonResponse


def main(request):
    return render(request, 'main.html')


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
