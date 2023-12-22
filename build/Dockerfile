FROM python:2

RUN pip install --no-cache-dir postmarkup

COPY Elements.py /usr/local/lib/python2.7/site-packages/
COPY ElementsSettings.txt /usr/local/lib/python2.7/site-packages/

ENTRYPOINT ["python"]
