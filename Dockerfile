FROM bailaohe/statoy:flask
MAINTAINER He Bai <bai.he@outlook.com>

RUN pip3 --no-cache-dir install parade==0.1.21
RUN pip3 --no-cache-dir install redis
RUN pip3 --no-cache-dir install beautifulsoup4
RUN pip3 --no-cache-dir install PyGithub
RUN pip3 --no-cache-dir install pymongo
RUN pip3 --no-cache-dir instlal flask_socketio

EXPOSE 5000

VOLUME /workspace

WORKDIR /workspace

CMD parade server
