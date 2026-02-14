# Usa uma imagem leve do Python
FROM python:3.9-slim

# Instala dependências do sistema (necessário para o PostgreSQL/psycopg2)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Define a pasta de trabalho dentro do container
WORKDIR /app

# Copia o arquivo de dependências e instala
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o código do bot para dentro do container
COPY . .

# Expõe a porta 5000 (apenas documental, o docker-compose que manda)
EXPOSE 5000

# Comando para rodar o bot (ATENÇÃO: Troque 'app.py' pelo nome do seu arquivo principal se for diferente)
CMD ["python", "app.py"]
