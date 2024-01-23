FROM python:2.7

RUN pip install --no-cache-dir postmarkup

COPY Elements.py /usr/local/lib/python2.7/site-packages/
COPY ElementsSettings.txt /usr/local/lib/python2.7/site-packages/

RUN apt-get update && apt-get install default-jre -y && apt-get clean

ENTRYPOINT ["python"]
