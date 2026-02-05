import streamlit as st
import requests
import qrcode
from io import BytesIO

# 1. CONFIGURACIÓN DE PÁGINA Y ESTILO PREMIUM (COLORES VIVOS)
st.set_page_config(page_title="Pagantodos", page_icon="🍽️", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    /* Fondo con gradiente para dar vida */
    .stApp { 
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); 
    }

    /* Tarjetas de Menú con Sombras Profundas */
    .menu-card {
        background: white;
        padding: 20px;
        border-radius: 20px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 10px 25px -5px rgba(0,0,0,0.1), 0 8px 10px -6px rgba(0,0,0,0.1);
        margin-bottom: 15px;
        border: 1px solid rgba(255,255,255,0.3);
    }
    
    .price-tag {
        color: #10b981;
        font-weight: 900;
        font-size: 1.3rem;
    }

    /* Botones de Pago Estilo Mercado Pago */
    .stLinkButton a {
        background: linear-gradient(90deg, #10b981 0%, #059669 100%) !important;
        color: white !important;
        border-radius: 15px !important;
        font-weight: 700 !important;
        padding: 18px !important;
        text-align: center !important;
        display: block !important;
        text-decoration: none !important;
        box-shadow: 0 10px 20px -5px rgba(16, 185, 129, 0.4) !important;
        transition: all 0.3s ease;
    }
    .stLinkButton a:hover {
        transform: scale(1.02);
        box-shadow: 0 15px 25px -5px rgba(16, 185, 129, 0.5) !important;
    }

    /* Caja de Ticket */
    .ticket-box {
        background: white;
        padding: 25px;
        border-radius: 25px;
        border-top: 8px solid #10b981;
        box-shadow: 0 20px 25px -5px rgba(0,0,0,0.1);
        color: #1e293b;
    }
    
    /* Sidebar Dark Mode */
    [data-testid="stSidebar"] { 
        background-color: #0f172a !important; 
    }
    [data-testid="stSidebar"] * { 
        color: white !important; 
    }

    /* Footer Style */
    .footer {
        text-align: center;
        padding: 30px;
        color: #64748b;
        font-size: 0.9rem;
        margin-top: 50px;
        border-top: 1px solid #cbd5e1;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. CREDENCIALES (Asegurate que estén en Streamlit Secrets)
TOKEN_AIRTABLE = st.secrets.get("AIRTABLE_TOKEN", "")
BASE_ID = st.secrets.get("AIRTABLE_BASE_ID", "")
MP_TOKEN = st.secrets.get("MP_ACCESS_TOKEN", "")
HEADERS = {"Authorization": f"Bearer {TOKEN_AIRTABLE}", "Content-Type": "application/json"}

# Captura de mesa desde la URL
nro_mesa = st.query_params.get("mesa", "1")

# 3. FUNCIONES DE DATOS (VELOCIDAD OPTIMIZADA)
@st.cache_data(ttl=30)
def obtener_menu():
    try:
        url = f"https://api.airtable.com/v0/{BASE_ID}/Menu"
        r = requests.get(url, headers=HEADERS)
        return r.json().get('records', [])
    except: return []

def crear_link_pago(titulo, monto):
    if not MP_TOKEN: return "https://www.mercadopago.com.ar"
    try:
        url = "https://api.mercadopago.com/checkout/preferences"
        h = {"Authorization": f"Bearer {MP_TOKEN}", "Content-Type": "application/json"}
        payload = {
            "items": [{"title": titulo, "quantity": 1, "unit_price": float(monto), "currency_id": "ARS"}],
            "back_urls": {"success": "https://pagantodos.streamlit.app/"},
            "auto_return": "approved"
        }
        res = requests.post(url, json=payload, headers=h)
        return res.json().get("init_point", "https://www.mercadopago.com.ar")
    except: return "https://www.mercadopago.com.ar"

# 4. SIDEBAR / CONTROL DE ACCESO
if "acceso_admin" not in st.session_state:
    st.session_state.acceso_admin = False

with st.sidebar:
    st.title("PAGANTODOS")
    st.markdown(f"### 📍 MESA ACTUAL: {nro_mesa}")
    st.write("---")
    modo_admin = st.toggle("🔐 Modo Administrador")
    
    if modo_admin:
        if not st.session_state.acceso_admin:
            clave = st.text_input("Clave de acceso", type="password")
            if clave == "pagantodos2026":
                st.session_state.acceso_admin = True
                st.rerun()
            elif clave != "":
                st.error("Clave incorrecta")
        else:
            st.success("Admin Identificado")
            if st.button("Cerrar Sesión"):
                st.session_state.acceso_admin = False
                st.rerun()

# 5. VISTA ADMINISTRADOR
if modo_admin and st.session_state.acceso_admin:
    st.title("⚙️ Panel de Administración")
    t1, t2, t3 = st.tabs(["📋 Comandas Activas", "🍔 Gestionar Menú", "📱 Generar QR"])

    with t1:
        st.subheader("Órdenes por Mesa")
        resp = requests.get(f"https://api.airtable.com/v0/{BASE_ID}/Pedidos", headers=HEADERS)
        pedidos = resp.json().get('records', [])
        
        if pedidos:
            # Agrupar pedidos por mesa para el botón de vaciar
            mesas_activas = sorted(list(set([p['fields'].get('Mesa', 1) for p in pedidos])))
            for m in mesas_activas:
                with st.expander(f"MESA {m}", expanded=True):
                    items_mesa = [p for p in pedidos if p['fields'].get('Mesa') == m]
                    for it in items_mesa:
                        col_p, col_b = st.columns([4, 1])
                        col_p.write(f"**{it['fields'].get('Usuario')}**: {it['fields'].get('Producto')} (${it['fields'].get('Precio')})")
                        # Borrado individual (Corregido el error de nodo)
                        if col_b.button("❌", key=f"del_{it['id']}"):
                            requests.delete(f"https://api.airtable.com/v0/{BASE_ID}/Pedidos/{it['id']}", headers=HEADERS)
                            st.rerun()
                    
                    st.write("---")
                    # BOTÓN VACIAR MESA COMPLETA
                    if st.button(f"🧹 VACIAR MESA {m}", key=f"vaciar_m_{m}"):
                        for it in items_mesa:
                            requests.delete(f"https://api.airtable.com/v0/{BASE_ID}/Pedidos/{it['id']}", headers=HEADERS)
                        st.success(f"Mesa {m} limpia")
                        st.rerun()
        else:
            st.info("No hay pedidos pendientes.")

    with t2:
        st.subheader("Cargar Producto Nuevo")
        with st.form("nuevo_producto"):
            n = st.text_input("Nombre")
            p = st.number_input("Precio", min_value=0)
            c = st.selectbox("Categoría", ["Entradas", "Principales", "Bebidas", "Postres"])
            img = st.text_input("Link de Imagen (URL)")
            if st.form_submit_button("Guardar en Menú"):
                data = {"fields": {"Producto": n, "Precio": p, "Categoria": c, "Imagen_Data": img}}
                requests.post(f"https://api.airtable.com/v0/{BASE_ID}/Menu", headers=HEADERS, json=data)
                st.cache_data.clear()
                st.success("¡Producto cargado!")
                st.rerun()

    with t3:
        st.subheader("Generador de QR")
        m_gen = st.number_input("Número de Mesa", min_value=1, value=1)
        url_final = f"https://pagantodos.streamlit.app/?mesa={m_gen}"
        st.code(url_final)
        
        qr = qrcode.QRCode(version=1, box_size=10, border=2)
        qr.add_data(url_final)
        qr.make(fit=True)
        img_qr = qr.make_image(fill_color="black", back_color="white")
        
        buf = BytesIO()
        img_qr.save(buf, format="PNG")
        st.image(buf.getvalue(), width=250)
        st.download_button("Descargar QR Mesa", buf.getvalue(), f"QR_Mesa_{m_gen}.png")

# 6. VISTA CLIENTE
else:
    if 'usuario' not in st.session_state:
        st.header("¡Bienvenido! 👋")
        st.write("Para comenzar a pedir, por favor ingresá tu nombre.")
        nombre = st.text_input("¿Cómo te llamás?")
        if st.button("INGRESAR") and nombre:
            st.session_state.usuario = nombre
            st.rerun()
    else:
        # Carga rápida del menú
        menu_items = obtener_menu()
        categorias = sorted(list(set([x['fields'].get('Categoria') for x in menu_items if x['fields'].get('Categoria')])))
        
        tabs = st.tabs(categorias + ["💳 MI CUENTA"])

        for i, cat in enumerate(categorias):
            with tabs[i]:
                for plato in [x for x in menu_items if x['fields'].get('Categoria') == cat]:
                    f = plato['fields']
                    st.markdown(f"""
                        <div class="menu-card">
                            <div style="display: flex; align-items: center; gap: 15px;">
                                <img src="{f.get('Imagen_Data','')}" width="75" height="75" style="border-radius:15px; object-fit:cover;">
                                <div>
                                    <div style="font-weight:700; font-size:1.1rem; color:#1e293b;">{f.get('Producto')}</div>
                                    <div class="price-tag">${f.get('Precio')}</div>
                                </div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    if st.button(f"Pedir {f.get('Producto')}", key=plato['id']):
                        pedido_data = {"fields": {
                            "Usuario": st.session_state.usuario, 
                            "Producto": f.get('Producto'), 
                            "Precio": float(f.get('Precio')), 
                            "Mesa": int(nro_mesa)
                        }}
                        requests.post(f"https://api.airtable.com/v0/{BASE_ID}/Pedidos", headers=HEADERS, json=pedido_data)
                        st.toast(f"¡{f.get('Producto')} agregado!")

        with tabs[-1]:
            st.markdown(f"## Estado de Cuenta - Mesa {nro_mesa}")
            res_pedidos = requests.get(f"https://api.airtable.com/v0/{BASE_ID}/Pedidos?filterByFormula=Mesa={nro_mesa}", headers=HEADERS)
            p_mesa = res_pedidos.json().get('records', [])
            
            col_1, col_2 = st.columns(2)
            with col_1:
                st.markdown("<div class='ticket-box'><h3>👤 MI PARTE</h3>", unsafe_allow_html=True)
                mios = [x for x in p_mesa if x['fields'].get('Usuario') == st.session_state.usuario]
                total_mio = sum([float(x['fields'].get('Precio', 0)) for x in mios])
                for p in mios: st.write(f"• {p['fields'].get('Producto')} (${p['fields'].get('Precio')})")
                st.markdown(f"<h3 style='color:#10b981'>Total: ${total_mio}</h3>", unsafe_allow_html=True)
                st.link_button(f"PAGAR MI CUENTA (MESA {nro_mesa})", crear_link_pago(f"Mesa {nro_mesa} - {st.session_state.usuario}", total_mio if total_mio > 0 else 1))
                st.markdown("</div>", unsafe_allow_html=True)

            with col_2:
                st.markdown("<div class='ticket-box'><h3>👥 TOTAL MESA</h3>", unsafe_allow_html=True)
                total_m = sum([float(x['fields'].get('Precio', 0)) for x in p_mesa])
                for p in p_mesa: st.write(f"• {p['fields'].get('Usuario')}: {p['fields'].get('Producto')}")
                st.markdown(f"<h3 style='color:#10b981'>Total: ${total_m}</h3>", unsafe_allow_html=True)
                st.link_button(f"PAGAR TODA LA MESA {nro_mesa}", crear_link_pago(f"Mesa {nro_mesa} - Total", total_m if total_m > 0 else 1))
                st.markdown("</div>", unsafe_allow_html=True)

# 7. FOOTER FINAL (Añadido)
st.markdown(f"""
    <div class="footer">
        <p><b>Pagantodos 2026</b> - Sistema Inteligente de Gestión Gastronómica</p>
        <p>Desarrollado para una experiencia sin esperas ❤️</p>
        <p style="font-size: 0.7rem; color: #94a3b8;">Propiedad exclusiva de Pagantodos. Todos los derechos reservados.</p>
    </div>
    """, unsafe_allow_html=True)