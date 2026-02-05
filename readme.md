# 🍽️ Pagantodos 2026 - Gestión Gastronómica Inteligente

**Pagantodos** es una aplicación web diseñada para revolucionar la experiencia en restaurantes. Permite a los comensales realizar pedidos desde su mesa mediante códigos QR, dividir la cuenta de forma equitativa o pagar el total, integrando pagos digitales y una gestión administrativa en tiempo real.

---

## 🚀 Funcionalidades Principales

### 📱 Para los Clientes
* **Acceso vía QR:** Identificación automática de la mesa mediante parámetros en la URL.
* **Menú Digital Dinámico:** Visualización de platos por categorías con imágenes y precios actualizados.
* **Pedidos en Tiempo Real:** Envío de comandas directamente a la cocina/administración.
* **División de Cuenta Inteligente:** Opción de pagar solo "mi parte" o el "total de la mesa".
* **Integración con Mercado Pago:** Generación de links de pago automáticos para una transacción segura.

### ⚙️ Para la Administración (Modo Admin)
* **Panel de Comandas:** Visualización y gestión de pedidos activos por mesa.
* **Gestión de Inventario:** Carga y edición de productos del menú directamente desde la app.
* **Generador de QR:** Herramienta integrada para crear y descargar los códigos QR de cada mesa.
* **Limpieza de Mesas:** Función para resetear los pedidos de una mesa una vez finalizado el servicio.

---

## 🛠️ Stack Tecnológico

* **Frontend/Backend:** [Streamlit](https://streamlit.io/) (Python).
* **Base de Datos:** [Airtable API](https://airtable.com/) (Tablas de `Menu` y `Pedidos`).
* **Pagos:** [Mercado Pago API](https://www.mercadopago.com.ar/developers).
* **Generación de QR:** Librería `qrcode` de Python.
* **Estilos:** CSS personalizado inyectado para una interfaz Premium.

---

## 📋 Requisitos Previos

Antes de correr la app, necesitás tener:
1.  Python 3.9 o superior instalado.
2.  Una cuenta en Airtable con una base que contenga las tablas `Menu` y `Pedidos`.
3.  Credenciales de Mercado Pago (Access Token).

---

## 💻 Instalación y Ejecución Local

1. **Clonar el repositorio:**
   ```bash
   git clone [https://github.com/DarioEmanuelVelez/App_pagantodos.git](https://github.com/DarioEmanuelVelez/App_pagantodos.git)
   cd App_pagantodos


Crear un entorno virtual:

Bash
python -m venv .venv
# Activar en Windows:
.venv\Scripts\activate

Instalar dependencias:

Bash
pip install streamlit requests qrcode pillow pandas


Configurar Secretos: Crea una carpeta .streamlit y dentro un archivo secrets.toml con el siguiente formato:

Ini, TOML
AIRTABLE_TOKEN = "tu_token_aquí"
AIRTABLE_BASE_ID = "tu_id_de_base"
MP_ACCESS_TOKEN = "tu_token_de_mercadopago"


Correr la aplicación:

Bash
streamlit run app.py

🌐 Despliegue
La aplicación está optimizada para ser desplegada en Streamlit Cloud. Asegúrate de configurar los Secrets en el panel de control de Streamlit con las mismas variables del archivo secrets.toml.

Desarrollado por Darío Emanuel Vélez - 2026


---

### Explicación Técnica (Para tu portafolio o curiosidad)

1.  **Arquitectura de Datos:** La app funciona de forma **asíncrona**. Cuando un cliente hace un pedido, se envía un `POST` a la API de Airtable. El Panel de Admin hace un `GET` constante para refrescar las comandas.
2.  **Manejo de Estados:** Utilizamos `st.session_state` para recordar el nombre del usuario durante su sesión, evitando que tenga que loguearse cada vez que navega por el menú.
3.  **Inyección de Estilos (CSS):** Para romper la estética estándar de Streamlit, se utilizó `st.markdown` con `unsafe_allow_html=True`, permitiendo crear tarjetas (`cards`) y botones con gradientes que responden al diseño móvil.
4.  **Parámetros de URL:** La función `st.query_params` es el motor de los QR. Al leer `?mesa=X`, la app filtra automáticamente todos los pedidos de la base de datos que coincidan con ese número, permitiendo que varios celulares "compartan" la misma mesa.



