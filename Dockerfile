FROM python:3.14-alpine as base
FROM base as builder
RUN mkdir /install
WORKDIR /ostorlab
COPY . /ostorlab
RUN pip install --upgrade pip
RUN pip install .[google-cloud-logging] --prefix=/install
RUN pip install .[agent] --prefix=/install
RUN pip install .[serve] --prefix=/install
RUN pip install .[scanner] --prefix=/install
FROM base
COPY --from=builder /install /usr/local
ENTRYPOINT ["ostorlab"]
