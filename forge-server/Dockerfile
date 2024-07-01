FROM python:3.10-slim

WORKDIR /review-forge
COPY . .
RUN pip install -r requirements.txt

CMD ["gunicorn", "-w", "4", "--bind", "0.0.0.0:5000", "wsgi:app"]
#CMD [ "python", "-m" , "flask", "run", "--host=0.0.0.0"]