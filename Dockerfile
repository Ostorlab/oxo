FROM python:3.10.14-alpine3.19 as base
FROM base as builder
RUN mkdir /install
WORKDIR /ostorlab
COPY . /ostorlab
RUN pip install .[google-cloud-logging] --prefix=/install
RUN pip install .[agent] --prefix=/install
FROM base
COPY --from=builder /install /usr/local
ENTRYPOINT ["ostorlab"]