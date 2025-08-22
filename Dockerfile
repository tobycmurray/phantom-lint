# syntax=docker/dockerfile:1

FROM python:3.11

RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    libgl1 \
    libglib2.0-0 \
    libdbus-1-3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libatspi2.0-0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libxkbcommon0 \
    libasound2 \
    libcups2 \
  && rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN useradd -ms /bin/bash phantomlint


WORKDIR /phantomlint

COPY . /phantomlint

RUN pip install -r requirements-frozen.txt
RUN pip install .

# Set ownership and permissions for the program
RUN chown -R phantomlint:phantomlint /phantomlint

# Switch to the non-root user
USER phantomlint

RUN playwright install

ENTRYPOINT [ "phantomlint" ]

CMD ["--help"]