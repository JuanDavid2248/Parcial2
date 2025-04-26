# Imagen base
FROM python:3.10

# Carpeta de trabajo en el contenedor
WORKDIR /app

# Copia los archivos de requisitos
COPY requirements.txt .

# Instala dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto de la app (aunque esto es opcional si usas volumen)
COPY . .

# Comando por defecto
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

