# 베이스 이미지
FROM python:3.9-slim

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 파일 복사 및 설치
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드 복사
COPY . /app/

# 포트 노출
EXPOSE 8000

# Django 서버 실행 명령
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

