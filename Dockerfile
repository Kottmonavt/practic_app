FROM python:3.8.19
WORKDIR /app

RUN python3 -m venv venv
ENV VIRTUAL_ENV=/app/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000
 
CMD [ "uvicorn", "--host", "0.0.0.0", "main:app" ]