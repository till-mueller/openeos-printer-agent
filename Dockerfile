FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libusb-1.0-0 \
        libjpeg62-turbo \
        gcc \
        python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# gcc/python3-dev above: psutil has no prebuilt wheel for every
# arm64/armv7 + CPython combo this image gets built for, so pip falls back
# to compiling it from source — python:3.11-slim ships no compiler by
# default. Needed at build time only; not removed afterward since apt
# layers don't shrink the final image without a multi-stage build, and this
# repo doesn't currently use one.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/
COPY templates/ templates/

RUN mkdir -p cache/templates config

EXPOSE 8080

ENTRYPOINT ["python", "-m", "src.main"]
CMD ["--config", "/app/config/config.yaml"]
