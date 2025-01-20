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
    credentials = request.session.get('credentials')
    if not credentials:
        return redirect('main')

    access_token = credentials.get('access_token')
    headers = {"Authorization": f"Bearer {access_token}"}
    events_url = "https://www.googleapis.com/calendar/v3/calendars/primary/events"

    response = requests.get(events_url, headers=headers)
    if response.status_code != 200:
        return JsonResponse({"error": "Failed to fetch events", "details": response.json()}, status=400)

    events = response.json().get('items', [])

    print("Events: ", events)

    return render(request, 'calendar.html', {"events": events})