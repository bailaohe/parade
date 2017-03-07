FROM bailaohe/python:flask
MAINTAINER He Bai <bai.he@outlook.com>

ADD src/ /parade/src
ADD setup.py /parade/setup.py
#ADD pip.conf /root/.pip/pip.conf
ADD requirements.txt /parade/requirements.txt

RUN cd /parade && pip3 --no-cache-dir install -r /requirements.txt --upgrade && python3 setup.py install && cd -

EXPOSE 5000
VOLUME /workspace

WORKDIR /workspace
CMD parade server
