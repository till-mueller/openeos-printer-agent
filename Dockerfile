FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libusb-1.0-0 \
        libjpeg62-turbo \
        gcc \
        python3-dev \
        zlib1g-dev \
        libjpeg62-turbo-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# gcc/python3-dev/zlib1g-dev/libjpeg62-turbo-dev above: psutil and Pillow
# don't have prebuilt wheels for every arm64/armv7 + CPython combo this
# image gets built for (armv7 especially — Pillow doesn't publish
# linux_armv7l wheels), so pip falls back to compiling them from source —
# python:3.11-slim ships neither a compiler nor image-library headers by
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
