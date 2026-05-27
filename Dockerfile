FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
	build-essential=12.9ubuntu3 \
	git \
	python-is-python3=3.9.2-2 \
	python3-pip=22.0.2+dfsg-1ubuntu0.7 \
	wget=1.21.2-2ubuntu1.1 \
	clang-15=1:15.0.7-0ubuntu0.22.04.3
RUN rm -rf /var/lib/apt/lists/*

COPY install_oclint.sh /tmp/install_oclint.sh
RUN chmod +x /tmp/install_oclint.sh && /tmp/install_oclint.sh

WORKDIR /app

ENV PATH="/opt/oclint/bin:${PATH}"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

ENTRYPOINT ["python", "-m", "src.main"]