# Guía de Despliegue en Producción

Esta guía detalla cómo desplegar el Dashboard de Accidentalidad Vial de Bogotá en un servidor de producción con HTTPS, usando Docker Compose, Traefik como reverse proxy y certificados SSL automáticos con Let's Encrypt.

## 📋 Tabla de Contenidos

* [Prerrequisitos](#-prerrequisitos)
* [Arquitectura del Despliegue](#️-arquitectura-del-despliegue)
* [Configuración Paso a Paso](#-configuración-paso-a-paso)
* [Variables de Entorno](#-variables-de-entorno)
* Seguridad

---

## 🔧 Prerrequisitos

**Requisitos del Servidor:**

* Máquina virtual o servidor en la nube (DigitalOcean, AWS, GCP, Azure, etc.)
* Sistema operativo: Ubuntu 20.04+ / Debian 11+ (recomendado)
* RAM mínima: 2 GB
* Espacio en disco: 10 GB mínimo
* Acceso root o sudo

**Software Necesario:**

* Docker 24.0+ y Docker Compose v2
* Dominio propio O usar servicios DNS gratuitos como sslip.io
* Puertos abiertos: 80 (HTTP) y 443 (HTTPS)

## 🏗️ Arquitectura del Despliegue

El stack de despliegue consta de dos servicios principales orquestados con Docker Compose:

```text
Internet
   ↓
[Puerto 80/443]
   ↓
[Traefik Reverse Proxy]
   ├─→ Gestión automática de certificados SSL (Let's Encrypt)
   ├─→ Redirección HTTP → HTTPS
   └─→ Routing basado en dominios
       ↓
[Dashboard Streamlit]
   └─→ Aplicación corriendo en puerto interno 8501
```

**Componentes:**

1. Traefik v3.6: Reverse proxy moderno con soporte para:
    * Renovación automática de certificados SSL/TLS
    * Enrutamiento dinámico basado en etiquetas Docker
    * Dashboard de monitoreo con autenticación básica
2. Dashboard Streamlit: Aplicación principal con análisis interactivo de datos

---

## 🚀 Configuración Paso a Paso

### 1. Preparar el Servidor

Conéctate a tu máquina virtual vía SSH:

```bash
# Si funciona con contraseña
ssh usuario@tu-ip-publica

# Si funciona keys
ssh -i /path/to/key usuario@tu-ip-publica
```

### 2. Configurar Variables de Entorno

Copia el archivo de ejemplo y edítalo con tus valores:

```bash
cp .env.example .env

# Editar el .env con tus propias credenciales
# (cambiar dominio, usuario, contraseña, etc.)
nano .env
```

Contenido del .env

```env
# Dominio base (sin subdominios)
# Opción 1: Dominio propio
DOMAIN=tudominio.com

# Opción 2: Servicio DNS gratuito (reemplaza con tu IP pública)
# DOMAIN=123-45-67-89.sslip.io

# Email para notificaciones de Let's Encrypt
LETSENCRYPT_EMAIL=tu-email@example.com

# Credenciales para el dashboard de Traefik
USERNAME=admin

# Password hasheado (ver sección de Seguridad para generarlo)
HASHED_PASSWORD='$$apr1$$xyz123$$hashaquigenerado'
```

### 3. Crear el archivo docker-compose.yml

Opción A - **Copiar desde el repositorio:**

```bash
# Clonar el repositorio
git clone https://github.com/dosquisd/AccidentalRiskAnalysis.git
cd AccidentalRiskAnalysis/deployment

# Los archivos ya están listos
```

Opción B - **Crear manualmente:**

```bash
nano docker-compose.yml
```

Pega el contenido completo del archivo `docker-compose.yml` que se encuentra en este directorio.

### 4. Configurar DNS

Opción A - **Dominio Propio:**

Crea registros DNS tipo A en tu proveedor de dominios:

```text
Tipo    Nombre              Valor (IP)          TTL
A       dashboard           123.45.67.89        3600
A       traefik             123.45.67.89        3600
```

Opción B - **sslip.io** (Para Testing/Desarrollo)

No requiere configuración DNS. Simplemente usa tu IP pública con el formato:

```text
# Formato: IP-SEPARADA-POR-GUIONES.sslip.io
# Ejemplo para IP 123.45.67.89
DOMAIN=123-45-67-89.sslip.io
```

El dominio `dashboard.123-45-67-89.sslip.io` resolverá automáticamente a `123.45.67.89`.

### 5. Iniciar el Stack

```bash
# Primera vez: Descargar imágenes e iniciar
docker compose up --build -d

# Ver logs en tiempo real
docker compose logs -f

# Verificar estado de los contenedores
docker compose ps
```

### 6. Verificar el Despliegue

Espera 30-60 segundos para que Let's Encrypt genere los certificados y luego accede a:

* Dashboard Principal: `https://dashboard.tudominio.com` (o `https://dashboard.123-45-67-89.sslip.io`)
* Traefik Dashboard: `https://traefik.tudominio.com` (requiere usuario/contraseña)

Si todo está correcto, verás:

* ✅ Conexión HTTPS segura (candado verde)
* ✅ Redirección automática de HTTP → HTTPS
* ✅ Dashboard de Streamlit funcionando

---

## 🔐 Variables de Entorno

### DOMAIN

El dominio base sin protocolo ni subdominios.

**Ejemplos válidos:**

```env
DOMAIN=example.com
DOMAIN=98-84-186-36.sslip.io
```

**Ejemplos inválidos:**

```env
DOMAIN=https://example.com    # ❌ No incluir protocolo
```

### LETSENCRYPT_EMAIL

Email para recibir notificaciones de Let's Encrypt sobre:

* Vencimiento de certificados
* Problemas de renovación
* Avisos de seguridad

### USERNAME y HASHED_PASSWORD

Credenciales para acceder al dashboard administrativo de Traefik (`https://traefik.tudominio.com`).

```bash
# Instalar htpasswd (si no está instalado)
sudo apt-get install apache2-utils

# Generar hash (reemplaza 'admin' y 'tupassword')
htpasswd -nb admin tupassword

# Output ejemplo:
# admin:$apr1$xyz123$hashaquigenerado
```

Copia TODO el hash después de los dos puntos y colócalo en .env con comillas simples y doble signo de dólar:

```env
HASHED_PASSWORD='$$apr1$$xyz123$$hashaquigenerado'
```

**⚠️ Importante:**

Usa comillas simples '...' para evitar que bash interprete los $
Duplica cada $ → $$ para Docker Compose
NO incluyas el username en el hash, solo lo que viene después de :

---

## 🔒 Seguridad

### Recomendaciones de Producción

#### 1. Firewall

```bash
# Configurar UFW (Ubuntu Firewall)
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

#### 2. Actualizar regularmente

```bash
# Actualizar imágenes Docker
docker compose pull
docker compose up -d

# Actualizar el sistema
sudo apt update && sudo apt upgrade -y
```

<!-- Para actualizar este proceso se pueden crear scripts propios agregar imagenes al stack que permitan actualizar las imagenes automaticamente -->

#### 3. Monitoreo

```bash
# Verificar uso de recursos
docker stats

# Verificar espacio en disco
df -h

# Ver certificados válidos
docker compose exec traefik ls -la /certificates/
```

#### 4. Cambiar contraseñas predeterminadas

* Genera passwords únicos y seguros
* No uses password o admin como contraseña
* Considera usar un gestor de contraseñas

---

## 📚 Recursos adicionales

* [Documentación de Traefik](https://doc.traefik.io/traefik/)
* [Let's Encrypt Rate Limits](https://letsencrypt.org/docs/rate-limits/)
* [Docker Compose Reference](https://docs.docker.com/reference/compose-file/)
* [Streamlit Deployment Guide](https://docs.streamlit.io/deploy)
