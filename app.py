import streamlit as st
import requests
import qrcode
import base64
from io import BytesIO

# 1. ESTÉTICA Y VISIBILIDAD (Texto Negro)
st.set_page_config(page_title="Pagantodos Premium", page_icon="🍽️", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: white !important; }
    input, textarea, [data-baseweb="select"] {
        background-color: #ffffff !important;
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
        border: 2px solid #334155 !important;
    }
    label, p, h1, h2, h3, span, .stMarkdown { color: #000000 !important; font-weight: 700 !important; }
    div.stButton > button {
        background: #10b981 !important; color: white !important;
        border-radius: 10px !important; font-weight: bold !important;
    }
    [data-testid="stSidebar"] { background-color: #0f172a !important; }
    [data-testid="stSidebar"] * { color: white !important; }
    .ticket-box {
        background: #f8fafc; padding: 20px; border-radius: 15px;
        border: 2px dashed #cbd5e1; margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. CREDENCIALES
TOKEN_AIRTABLE = st.secrets.get("AIRTABLE_TOKEN", "")
BASE_ID = st.secrets.get("AIRTABLE_BASE_ID", "")
MP_TOKEN = st.secrets.get("MP_ACCESS_TOKEN", "")
HEADERS = {"Authorization": f"Bearer {TOKEN_AIRTABLE}", "Content-Type": "application/json"}
nro_mesa = st.query_params.get("mesa", "1")

# 3. FUNCIONES
@st.cache_data(ttl=5)
def obtener_menu():
    try:
        r = requests.get(f"https://api.airtable.com/v0/{BASE_ID}/Menu", headers=HEADERS)
        return r.json().get('records', [])
    except: return []

def crear_link_pago(titulo, monto):
    if not MP_TOKEN: return "https://www.mercadopago.com.ar"
    try:
        payload = {
            "items": [{"title": titulo, "quantity": 1, "unit_price": float(monto), "currency_id": "ARS"}],
            "back_urls": {"success": "https://pagantodos.streamlit.app/"},
            "auto_return": "approved"
        }
        res = requests.post("https://api.mercadopago.com/checkout/preferences", json=payload, headers={"Authorization": f"Bearer {MP_TOKEN}"})
        return res.json().get("init_point", "https://www.mercadopago.com.ar")
    except: return "https://www.mercadopago.com.ar"

# 4. SIDEBAR
if "acceso_admin" not in st.session_state: st.session_state.acceso_admin = False

with st.sidebar:
    st.title("PAGANTODOS")
    st.info(f"📍 Mesa: {nro_mesa}")
    admin_mode = st.toggle("Modo Administrador")
    if admin_mode:
        if not st.session_state.acceso_admin:
            clave = st.text_input("Clave", type="password")
            if clave == "pagantodos2026":
                st.session_state.acceso_admin = True
                st.rerun()
        else:
            if st.button("Salir"):
                st.session_state.acceso_admin = False
                st.rerun()

# 5. VISTA ADMIN (Limpieza de Mesas Restaurada)
if admin_mode and st.session_state.acceso_admin:
    st.title("⚙️ Administración")
    t1, t2, t3 = st.tabs(["📋 Comandas", "🍔 Menú", "📱 QR"])

    with t1:
        st.subheader("Control de Pedidos")
        r_ped = requests.get(f"https://api.airtable.com/v0/{BASE_ID}/Pedidos", headers=HEADERS)
        todos = r_ped.json().get('records', [])
        mesas = sorted(list(set([p['fields'].get('Mesa', 1) for p in todos]))) if todos else []
        
        for m in mesas:
            with st.expander(f"🛒 MESA {m}", expanded=True):
                items_m = [p for p in todos if p['fields'].get('Mesa') == m]
                for it in items_m:
                    c1, c2 = st.columns([4, 1])
                    c1.write(f"**{it['fields'].get('Usuario')}**: {it['fields'].get('Producto')} (${it['fields'].get('Precio')})")
                    if c2.button("❌", key=f"del_{it['id']}"):
                        requests.delete(f"https://api.airtable.com/v0/{BASE_ID}/Pedidos/{it['id']}", headers=HEADERS)
                        st.rerun()
                st.write("---")
                if st.button(f"🔥 LIMPIAR MESA {m} COMPLETA", key=f"v_{m}"):
                    for it in items_m: requests.delete(f"https://api.airtable.com/v0/{BASE_ID}/Pedidos/{it['id']}", headers=HEADERS)
                    st.rerun()

    with t2:
        m_actual = obtener_menu()
        cats_reales = sorted(list(set([x['fields'].get('Categoria') for x in m_actual if x['fields'].get('Categoria')])))
        with st.form("carga"):
            n = st.text_input("Plato")
            p = st.number_input("Precio", min_value=0)
            c_s = st.selectbox("Categoría", cats_reales + ["+ Nueva"])
            c_n = st.text_input("Cuál?") if c_s == "+ Nueva" else ""
            cat_f = c_n if c_s == "+ Nueva" else c_s
            file = st.file_uploader("Subir foto", type=["jpg", "png", "jpeg"])
            if st.form_submit_button("GUARDAR"):
                b64 = f"data:image/png;base64,{base64.b64encode(file.getvalue()).decode()}" if file else ""
                requests.post(f"https://api.airtable.com/v0/{BASE_ID}/Menu", headers=HEADERS, json={"fields": {"Producto": n, "Precio": p, "Categoria": cat_f, "Imagen_Data": b64}})
                st.cache_data.clear()
                st.rerun()

    with t3:
        n_m = st.number_input("Mesa QR", min_value=1, value=1)
        link = f"https://pagantodos.streamlit.app/?mesa={n_m}"
        st.code(link)
        img = qrcode.make(link)
        buf = BytesIO(); img.save(buf, format="PNG")
        st.image(buf.getvalue(), width=250)

# 6. VISTA CLIENTE (Detalle de Cuenta Restaurado)
else:
    if 'usuario' not in st.session_state:
        st.title("🍽️ Bienvenido")
        u = st.text_input("Tu nombre")
        if st.button("ENTRAR") and u:
            st.session_state.usuario = u
            st.rerun()
    else:
        m_items = obtener_menu()
        cats = sorted(list(set([x['fields'].get('Categoria') for x in m_items if x['fields'].get('Categoria')])))
        tabs = st.tabs(cats + ["💳 MI CUENTA"])
        
        for i, c in enumerate(cats):
            with tabs[i]:
                for p in [x for x in m_items if x['fields'].get('Categoria') == c]:
                    f = p['fields']
                    col_i, col_t = st.columns([1, 3])
                    if f.get("Imagen_Data"): col_i.image(f.get("Imagen_Data"), width=100)
                    col_t.write(f"**{f.get('Producto')}** - ${f.get('Precio')}")
                    if col_t.button(f"Pedir {f.get('Producto')}", key=p['id']):
                        requests.post(f"https://api.airtable.com/v0/{BASE_ID}/Pedidos", headers=HEADERS, json={"fields": {"Usuario": st.session_state.usuario, "Producto": f.get('Producto'), "Precio": float(f.get('Precio')), "Mesa": int(nro_mesa)}})
                        st.toast("Pedido enviado")

        with tabs[-1]:
            st.header("📄 Detalle de Consumo")
            res_p = requests.get(f"https://api.airtable.com/v0/{BASE_ID}/Pedidos?filterByFormula=Mesa={nro_mesa}", headers=HEADERS)
            pedidos_mesa = res_p.json().get('records', [])

            c1, c2 = st.columns(2)
            with c1:
                st.subheader("👤 Mi Parte")
                mis_items = [x for x in pedidos_mesa if x['fields'].get('Usuario') == st.session_state.usuario]
                total_yo = 0
                for mi in mis_items:
                    st.write(f"- {mi['fields'].get('Producto')}: ${mi['fields'].get('Precio')}")
                    total_yo += float(mi['fields'].get('Precio', 0))
                st.markdown(f"### Total: ${total_yo}")
                st.link_button("PAGAR MI PARTE", crear_link_pago(f"Mesa {nro_mesa} - {st.session_state.usuario}", total_yo if total_yo > 0 else 1))

            with c2:
                st.subheader("👥 Total Mesa")
                total_m = 0
                for pm in pedidos_mesa:
                    st.write(f"- {pm['fields'].get('Usuario')}: {pm['fields'].get('Producto')} (${pm['fields'].get('Precio')})")
                    total_m += float(pm['fields'].get('Precio', 0))
                st.markdown(f"### Total Mesa: ${total_m}")
                st.link_button("PAGAR TOTAL MESA", crear_link_pago(f"Mesa {nro_mesa} - Total", total_m if total_m > 0 else 1))

st.markdown("---")
st.write("Pagantodos 2026")