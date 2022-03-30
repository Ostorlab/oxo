FROM python:3.9-bullseye as base
FROM base as builder
RUN mkdir /install
WORKDIR /install
RUN pip install --prefix=/install ostorlab
FROM base
COPY --from=builder /install /usr/local
RUN mkdir -p /app/agent
ENTRYPOINT ["ostorlab"]