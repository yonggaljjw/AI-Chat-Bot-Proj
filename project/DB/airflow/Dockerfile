FROM apache/airflow:2.5.1-python3.8

USER root

RUN apt-get update && \
    apt-get install -y build-essential default-libmysqlclient-dev && \
    apt-get install -y openjdk-17-jre && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*



# Java 환경 변수 설정
# ENV JAVA_HOME /usr/lib/jvm/java-17-openjdk-amd64
# ENV PATH $JAVA_HOME/bin:$PATH
# airflow 사용자로 변경
USER airflow
# 필요한 Python 패키지 설치
RUN pip install --no-cache-dir \
    yfinance \
    pandas \
    numpy \
    oauth2client \
    gspread \
    mysqlclient \
    fredapi \
    PublicDataReader \
    elasticsearch \
    eland \
    prophet==1.1.6 \
    plotly \
    dash==2.9.3 \
    konlpy==0.6.0 \
    wordcloud==1.9.2 \
    gensim


CMD ["webserver"]