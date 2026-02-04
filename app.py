import streamlit as st
import requests
import qrcode
from io import BytesIO

# 1. CONFIGURACIÓN Y ESTILOS
st.set_page_config(page_title="Pagantodos", page_icon="🍽️", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f8fafc; }
    [data-testid="stSidebar"] { background-color: #0f172a !important; }
    .stLinkButton a {
        background: linear-gradient(90deg, #22c55e 0%, #16a34a 100%) !important;
        color: white !important;
        border-radius: 12px !important;
        font-weight: 800 !important;
        padding: 15px !important;
        text-align: center !important;
        text-decoration: none !important;
        display: block !important;
    }
    .menu-card {
        background: white; padding: 15px; border-radius: 15px;
        display: flex; align-items: center; justify-content: space-between;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-bottom: 10px;
        color: #1e293b;
    }
    .ticket-box {
        background: white; padding: 20px; border-radius: 20px;
        border-top: 5px solid #22c55e; color: #1e293b;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# 2. CREDENCIALES
TOKEN_AIRTABLE = st.secrets.get("AIRTABLE_TOKEN", "")
BASE_ID = st.secrets.get("AIRTABLE_BASE_ID", "")
MP_TOKEN = st.secrets.get("MP_ACCESS_TOKEN", "")
HEADERS_AIRTABLE = {"Authorization": f"Bearer {TOKEN_AIRTABLE}", "Content-Type": "application/json"}
nro_mesa = st.query_params.get("mesa", "1")

# 3. FUNCIONES AUXILIARES
def crear_link_pago(titulo, monto):
    if not MP_TOKEN: return "https://www.mercadopago.com.ar"
    try:
        url_mp = "https://api.mercadopago.com/checkout/preferences"
        headers_mp = {"Authorization": f"Bearer {MP_TOKEN}", "Content-Type": "application/json"}
        payload = {
            "items": [{"title": titulo, "quantity": 1, "unit_price": float(monto), "currency_id": "ARS"}],
            "back_urls": {"success": "https://share.streamlit.io/"}, "auto_return": "approved"
        }
        res = requests.post(url_mp, json=payload, headers=headers_mp, timeout=10)
        return res.json().get("init_point", "https://www.mercadopago.com.ar")
    except: return "https://www.mercadopago.com.ar"

def generar_qr(url):
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

# 4. SIDEBAR LOGIC
if "acceso_admin" not in st.session_state:
    st.session_state.acceso_admin = False

with st.sidebar:
    st.title("PAGANTODOS")
    modo_admin = st.toggle("🔐 Modo Admin")
    if modo_admin:
        if not st.session_state.acceso_admin:
            clave = st.text_input("Clave", type="password")
            if clave == "pagantodos2026":
                st.session_state.acceso_admin = True
                st.rerun()
        else:
            st.success("Admin Activo")
            if st.button("Salir"):
                st.session_state.acceso_admin = False
                st.rerun()
    else:
        st.success(f"📍 Mesa {nro_mesa}")

# 5. VISTA ADMIN
if modo_admin and st.session_state.acceso_admin:
    st.title("⚙️ Panel de Control")
    t1, t2, t3 = st.tabs(["📋 Pedidos", "🍔 Menú", "📱 QR Mesas"])
    
    with t1:
        res_p = requests.get(f"https://api.airtable.com/v0/{BASE_ID}/Pedidos", headers=HEADERS_AIRTABLE)
        pedidos = res_p.json().get('records', [])
        for p in pedidos:
            f = p['fields']
            c1, c2 = st.columns([4,1])
            c1.write(f"Mesa {f.get('Mesa')} | {f.get('Usuario')}: {f.get('Producto')} (${f.get('Precio')})")
            if c2.button("❌", key=p['id']):
                requests.delete(f"https://api.airtable.com/v0/{BASE_ID}/Pedidos/{p['id']}", headers=HEADERS_AIRTABLE)
                st.rerun()

    with t2:
        with st.form("nuevo"):
            p1 = st.text_input("Producto")
            p2 = st.number_input("Precio", min_value=0)
            p3 = st.selectbox("Categoría", ["Entradas", "Principales", "Bebidas", "Postres"])
            p4 = st.text_input("URL Imagen")
            if st.form_submit_button("Cargar"):
                requests.post(f"https://api.airtable.com/v0/{BASE_ID}/Menu", headers=HEADERS_AIRTABLE, json={"fields": {"Producto": p1, "Precio": p2, "Categoria": p3, "Imagen_Data": p4}})
                st.success("¡Cargado!")
                st.rerun()

    with t3:
        n_mesa = st.number_input("Número de Mesa", min_value=1, value=1)
        url_mesa = f"https://darioemanuelvelez-app-pagantodos-app-h1v0i4.streamlit.app/?mesa={n_mesa}"
        st.code(url_mesa)
        st.image(generar_qr(url_mesa), caption=f"QR Mesa {n_mesa}")

# 6. VISTA CLIENTE
else:
    if 'usuario' not in st.session_state:
        st.header("Bienvenido")
        nombre = st.text_input("Tu nombre")
        if st.button("Entrar") and nombre:
            st.session_state.usuario = nombre
            st.rerun()
    else:
        res_m = requests.get(f"https://api.airtable.com/v0/{BASE_ID}/Menu", headers=HEADERS_AIRTABLE)
        items = res_m.json().get('records', [])
        categorias = sorted(list(set([x['fields'].get('Categoria', 'Varios') for x in items if x['fields'].get('Categoria')])))
        tabs = st.tabs(categorias + ["💳 MI CUENTA"])

        for i, cat in enumerate(categorias):
            with tabs[i]:
                for it in [x for x in items if x['fields'].get('Categoria') == cat]:
                    f = it['fields']
                    st.markdown(f"""<div class="menu-card"><div><b>{f.get('Producto')}</b><br>${f.get('Precio')}</div><img src="{f.get('Imagen_Data','')}" width="70" style="border-radius:10px"></div>""", unsafe_allow_html=True)
                    if st.button(f"Pedir {f.get('Producto')}", key=it['id']):
                        requests.post(f"https://api.airtable.com/v0/{BASE_ID}/Pedidos", headers=HEADERS_AIRTABLE, json={"fields": {"Usuario": st.session_state.usuario, "Producto": f.get('Producto'), "Precio": float(f.get('Precio', 0)), "Mesa": int(nro_mesa)}})
                        st.toast("¡Pedido enviado!")

        with tabs[-1]:
            res_c = requests.get(f"https://api.airtable.com/v0/{BASE_ID}/Pedidos?filterByFormula=Mesa={nro_mesa}", headers=HEADERS_AIRTABLE)
            p_mesa = res_c.json().get('records', [])
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("<div class='ticket-box'><h4>👤 MI PARTE</h4>", unsafe_allow_html=True)
                m = [x for x in p_mesa if x['fields'].get('Usuario') == st.session_state.usuario]
                t = sum([float(x['fields'].get('Precio', 0)) for x in m])
                for p in m: st.write(f"- {p['fields'].get('Producto')}")
                st.write(f"**Total: ${t}**")
                st.link_button("PAGAR", crear_link_pago("Mi parte", t if t > 0 else 1))
                st.markdown("</div>", unsafe_allow_html=True)
            with c2:
                st.markdown("<div class='ticket-box'><h4>👥 MESA</h4>", unsafe_allow_html=True)
                tm = sum([float(x['fields'].get('Precio', 0)) for x in p_mesa])
                for p in p_mesa: st.write(f"- {p['fields'].get('Usuario')}: {p['fields'].get('Producto')}")
                st.write(f"**Total: ${tm}**")
                st.link_button("PAGAR TODO", crear_link_pago("Mesa completa", tm if tm > 0 else 1))
                st.markdown("</div>", unsafe_allow_html=True)

# 7. FOOTER
st.markdown("<br><hr><center><small>Propiedad de <b>Pagantodos 2026</b></small></center>", unsafe_allow_html=True)