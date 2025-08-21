FROM python:3.9-slim

# Instalar dependências do sistema essenciais
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgtk-3-dev \
    gfortran \
    curl \
    wget \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgthread-2.0-0 \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    libxvidcore-dev \
    libx264-dev \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    && rm -rf /var/lib/apt/lists/*

# Definir diretório de trabalho
WORKDIR /app

# Copiar arquivos de dependências
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY sistema_acesso_funcionarios.py .
COPY templates/ templates/
COPY static/ static/

# Criar diretório de logs
RUN mkdir -p logs

# Definir variáveis de ambiente
ENV PYTHONPATH=/app
ENV TZ=America/Sao_Paulo

# Expor porta
EXPOSE 8082

# Comando para executar a aplicação
CMD ["python", "sistema_acesso_funcionarios.py"]
