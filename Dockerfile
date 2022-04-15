FROM python:3.9-bullseye as base
FROM base as builder
RUN mkdir /install
WORKDIR /ostorlab
COPY . /ostorlab
RUN pip install .[agent] --prefix=/install
FROM base
COPY --from=builder /install /usr/local
ENTRYPOINT ["ostorlab"]