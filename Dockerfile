FROM bailaohe/python:flask
MAINTAINER He Bai <bai.he@outlook.com>

RUN pip3 --no-cache-dir install parade --upgrade && cd -

EXPOSE 5000

VOLUME /workspace

WORKDIR /workspace

CMD parade server
