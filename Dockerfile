FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
	python3 \
	python3-pip \
	python3-venv \
	wget \
	&& rm -rf /var/lib/apt/lists/*

COPY install_oclint.sh /tmp/install_oclint.sh
RUN chmod +x /tmp/install_oclint.sh && /tmp/install_oclint.sh

WORKDIR /app

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:/opt/oclint/bin:${PATH}"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

ENTRYPOINT ["python", "-m", "src.main"]