import streamlit as st
import requests
import base64
from io import BytesIO
from PIL import Image

# 1. ESTILOS CSS (FORZANDO VISIBILIDAD)
st.set_page_config(page_title="Pagantodos", page_icon="🍽️", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f8fafc; }
    [data-testid="stSidebar"] { background-color: #0f172a !important; }
    
    /* FORZAR ESTILO DE BOTONES DE PAGO */
    .stLinkButton a {
        background: linear-gradient(90deg, #22c55e 0%, #16a34a 100%) !important;
        color: white !important;
        border-radius: 12px !important;
        font-weight: 800 !important;
        padding: 15px !important;
        text-align: center !important;
        text-decoration: none !important;
        display: block !important;
        margin-top: 10px !important;
    }
    
    .ticket-box {
        background: white; padding: 20px; border-radius: 20px;
        border: 1px solid #e2e8f0; border-top: 5px solid #22c55e;
        color: #1e293b;
    }
    
    .menu-card {
        background: white; padding: 15px; border-radius: 15px;
        display: flex; align-items: center; justify-content: space-between;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. CREDENCIALES
TOKEN_AIRTABLE = st.secrets.get("AIRTABLE_TOKEN", "")
BASE_ID = st.secrets.get("AIRTABLE_BASE_ID", "")
MP_TOKEN = st.secrets.get("MP_ACCESS_TOKEN", None) 
HEADERS_AIRTABLE = {"Authorization": f"Bearer {TOKEN_AIRTABLE}", "Content-Type": "application/json"}
nro_mesa = st.query_params.get("mesa", "1")

# --- LÓGICA DE PAGO ---
def crear_link_pago(titulo, monto):
    if not MP_TOKEN: return "https://mercadopago.com.ar" # Link de backup
    try:
        url_mp = "https://api.mercadopago.com/checkout/preferences"
        headers_mp = {"Authorization": f"Bearer {MP_TOKEN}", "Content-Type": "application/json"}
        payload = {
            "items": [{"title": titulo, "quantity": 1, "unit_price": float(monto), "currency_id": "ARS"}],
            "back_urls": {"success": "https://tu-app.streamlit.app"}, "auto_return": "approved"
        }
        res = requests.post(url_mp, json=payload, headers=headers_mp, timeout=10)
        return res.json().get("init_point", "https://mercadopago.com.ar")
    except: return "https://mercadopago.com.ar"

# --- SIDEBAR ---
with st.sidebar:
    st.title("PAGANTODOS")
    modo_admin = st.toggle("🔐 Modo Admin")
    acceso_concedido = False
    if modo_admin:
        if st.text_input("Clave", type="password") == "pagantodos2026": acceso_concedido = True
    else: st.success(f"Mesa {nro_mesa}")

# --- VISTA ADMIN ---
if modo_admin and acceso_concedido:
    st.write("Panel de control activo")
    # (Aquí iría la lógica de carga de menú que ya tienes)

# --- VISTA CLIENTE ---
elif not modo_admin:
    if 'usuario' not in st.session_state:
        nombre = st.text_input("Tu nombre")
        if st.button("ENTRAR"):
            if nombre: st.session_state.usuario = nombre; st.rerun()
    else:
        # Cargar Menú
        res_m = requests.get(f"https://api.airtable.com/v0/{BASE_ID}/Menu", headers=HEADERS_AIRTABLE)
        items = res_m.json().get('records', [])
        
        cats = sorted(list(set([x['fields'].get('Categoria', 'Varios') for x in items if x['fields'].get('Categoria')])))
        tabs = st.tabs(cats + ["💳 PAGAR"])

        for i, cat in enumerate(cats):
            with tabs[i]:
                for it in [x for x in items if x['fields'].get('Categoria') == cat]:
                    f = it['fields']
                    st.markdown(f"""<div class="menu-card"><div><b>{f.get('Producto')}</b><br>${f.get('Precio')}</div>
                    <img src="{f.get('Imagen_Data','')}" width="80" style="border-radius:10px"></div>""", unsafe_allow_html=True)
                    if st.button(f"PEDIR {f.get('Producto')}", key=it['id']):
                        requests.post(f"https://api.airtable.com/v0/{BASE_ID}/Pedidos", headers=HEADERS_AIRTABLE, json={"records": [{"fields": {"Usuario": st.session_state.usuario, "Producto": f.get('Producto'), "Precio": float(f.get('Precio', 0)), "Mesa": int(nro_mesa), "Estado": "Pendiente"}}]})
                        st.toast("Pedido enviado!")

        # --- PESTAÑA DE PAGOS SIN CONDICIONES ---
        with tabs[-1]:
            res_c = requests.get(f"https://api.airtable.com/v0/{BASE_ID}/Pedidos?filterByFormula=AND(Mesa={nro_mesa},Estado='Pendiente')", headers=HEADERS_AIRTABLE)
            pedidos_mesa = res_c.json().get('records', [])
            
            c1, c2 = st.columns(2)
            
            with c1:
                st.markdown("<div class='ticket-box'><h4>👤 MI PARTE</h4>", unsafe_allow_html=True)
                mios = [x for x in pedidos_mesa if x['fields'].get('Usuario') == st.session_state.usuario]
                total_mio = sum([float(x['fields'].get('Precio', 0)) for x in mios])
                for p in mios: st.write(f"- {p['fields'].get('Producto')}")
                st.write(f"**Total: ${total_mio}**")
                st.markdown("</div>", unsafe_allow_html=True)
                
                # BOTÓN FORZADO: Sin 'if', se tiene que ver sí o sí
                link_m = crear_link_pago("Mi parte", total_mio if total_mio > 0 else 1)
                st.link_button("PAGAR MI PARTE 💳", link_m, use_container_width=True)

            with c2:
                st.markdown("<div class='ticket-box'><h4>👥 LA MESA</h4>", unsafe_allow_html=True)
                total_mesa = sum([float(x['fields'].get('Precio', 0)) for x in pedidos_mesa])
                for p in pedidos_mesa: st.write(f"- {p['fields'].get('Usuario')}: {p['fields'].get('Producto')}")
                st.write(f"**Total: ${total_mesa}**")
                st.markdown("</div>", unsafe_allow_html=True)
                
                # BOTÓN FORZADO
                link_t = crear_link_pago("Total Mesa", total_mesa if total_mesa > 0 else 1)
                st.link_button("PAGAR TODA LA MESA 💳", link_t, use_container_width=True)