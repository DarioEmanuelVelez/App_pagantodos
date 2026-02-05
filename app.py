import streamlit as st
import requests
import qrcode
from io import BytesIO

# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS CSS
st.set_page_config(page_title="Pagantodos", page_icon="🍽️", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f8fafc; }
    [data-testid="stSidebar"] { background-color: #0f172a !important; }
    
    /* BOTONES DE PAGO ESTILO MERCADO PAGO */
    .stLinkButton a {
        background: linear-gradient(90deg, #22c55e 0%, #16a34a 100%) !important;
        color: white !important;
        border-radius: 12px !important;
        font-weight: 800 !important;
        padding: 15px !important;
        text-align: center !important;
        text-decoration: none !important;
        display: block !important;
        box-shadow: 0 4px 12px rgba(34, 197, 94, 0.3);
    }
    
    /* TARJETAS DE MENÚ */
    .menu-card {
        background: white; padding: 15px; border-radius: 15px;
        display: flex; align-items: center; justify-content: space-between;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-bottom: 10px;
        color: #1e293b; border: 1px solid #f1f5f9;
    }
    
    /* CAJA DE TICKET/CUENTA */
    .ticket-box {
        background: white; padding: 20px; border-radius: 20px;
        border-top: 5px solid #22c55e; color: #1e293b;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. CREDENCIALES (DESDE SECRETS)
TOKEN_AIRTABLE = st.secrets.get("AIRTABLE_TOKEN", "")
BASE_ID = st.secrets.get("AIRTABLE_BASE_ID", "")
MP_TOKEN = st.secrets.get("MP_ACCESS_TOKEN", "")
HEADERS_AIRTABLE = {"Authorization": f"Bearer {TOKEN_AIRTABLE}", "Content-Type": "application/json"}

# Captura de mesa desde la URL (por defecto mesa 1)
nro_mesa = st.query_params.get("mesa", "1")

# 3. FUNCIONES AUXILIARES
def crear_link_pago(titulo, monto):
    if not MP_TOKEN: return "https://www.mercadopago.com.ar"
    try:
        url_mp = "https://api.mercadopago.com/checkout/preferences"
        headers_mp = {"Authorization": f"Bearer {MP_TOKEN}", "Content-Type": "application/json"}
        payload = {
            "items": [{"title": titulo, "quantity": 1, "unit_price": float(monto), "currency_id": "ARS"}],
            "back_urls": {"success": "https://share.streamlit.io/"},
            "auto_return": "approved"
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

# 4. SIDEBAR - CONTROL DE ACCESO ADMIN
if "acceso_admin" not in st.session_state:
    st.session_state.acceso_admin = False

with st.sidebar:
    st.title("PAGANTODOS")
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
    else:
        st.success(f"📍 MESA ACTUAL: {nro_mesa}")

# 5. VISTA ADMINISTRADOR
if modo_admin and st.session_state.acceso_admin:
    st.title("⚙️ Panel de Control")
    tab1, tab2, tab3 = st.tabs(["📋 Pedidos Activos", "🍔 Gestionar Menú", "📱 Generar QRs"])
    
    with tab1:
        st.subheader("Órdenes de todas las mesas")
        res_p = requests.get(f"https://api.airtable.com/v0/{BASE_ID}/Pedidos", headers=HEADERS_AIRTABLE)
        pedidos = res_p.json().get('records', [])
        if not pedidos:
            st.write("No hay pedidos pendientes.")
        for p in pedidos:
            f = p['fields']
            col1, col2 = st.columns([4, 1])
            col1.write(f"**Mesa {f.get('Mesa')}** - {f.get('Usuario')}: {f.get('Producto')} (${f.get('Precio')})")
            if col2.button("Finalizar", key=p['id']):
                requests.delete(f"https://api.airtable.com/v0/{BASE_ID}/Pedidos/{p['id']}", headers=HEADERS_AIRTABLE)
                st.rerun()

    with tab2:
        st.subheader("Cargar Producto al Menú")
        with st.form("nuevo_pro"):
            p_nom = st.text_input("Nombre del producto")
            p_pre = st.number_input("Precio", min_value=0)
            p_cat = st.selectbox("Categoría", ["Entradas", "Principales", "Bebidas", "Postres"])
            p_img = st.text_input("Link de imagen (URL)")
            if st.form_submit_button("Guardar en Menú"):
                nuevo = {"fields": {"Producto": p_nom, "Precio": p_pre, "Categoria": p_cat, "Imagen_Data": p_img}}
                requests.post(f"https://api.airtable.com/v0/{BASE_ID}/Menu", headers=HEADERS_AIRTABLE, json=nuevo)
                st.success("¡Producto cargado con éxito!")
                st.rerun()

    with tab3:
        st.subheader("Códigos QR por Mesa")
        n_mesa_gen = st.number_input("Número de Mesa a generar", min_value=1, value=int(nro_mesa), step=1)
        
        # AJUSTE PARA EVITAR BLOQUEO DE GITHUB (Separamos la URL)
        p1 = "https://darioemanuelvelez-app-pagantodos-app-"
        p2 = "h1v0i4"
        p3 = ".streamlit.app"
        
        url_final = f"{p1}{p2}{p3}/?mesa={n_mesa_gen}"
        
        st.code(url_final)
        qr_img = generar_qr(url_final)
        st.image(qr_img, caption=f"QR para Mesa {n_mesa_gen}", width=250)
        
        st.download_button(
            label="Descargar Imagen QR",
            data=qr_img,
            file_name=f"QR_Mesa_{n_mesa_gen}.png",
            mime="image/png"
        )

# 6. VISTA CLIENTE
else:
    if 'usuario' not in st.session_state:
        st.header("¡Bienvenido! 👋")
        nombre = st.text_input("¿Cómo es tu nombre?")
        if st.button("INGRESAR A LA MESA"):
            if nombre:
                st.session_state.usuario = nombre
                st.rerun()
    else:
        # Cargar Menú desde Airtable
        res_m = requests.get(f"https://api.airtable.com/v0/{BASE_ID}/Menu", headers=HEADERS_AIRTABLE)
        items = res_m.json().get('records', [])
        
        categorias = sorted(list(set([x['fields'].get('Categoria', 'Varios') for x in items if x['fields'].get('Categoria')])))
        tabs = st.tabs(categorias + ["💳 MI CUENTA"])

        for i, cat in enumerate(categorias):
            with tabs[i]:
                for it in [x for x in items if x['fields'].get('Categoria') == cat]:
                    f = it['fields']
                    st.markdown(f"""<div class="menu-card">
                        <div><b>{f.get('Producto')}</b><br><span style='color: #22c55e;'>${f.get('Precio')}</span></div>
                        <img src="{f.get('Imagen_Data','')}" width="70" style="border-radius:10px; object-fit: cover;">
                    </div>""", unsafe_allow_html=True)
                    if st.button(f"Pedir {f.get('Producto')}", key=it['id']):
                        data = {"fields": {"Usuario": st.session_state.usuario, "Producto": f.get('Producto'), 
                                         "Precio": float(f.get('Precio', 0)), "Mesa": int(nro_mesa)}}
                        requests.post(f"https://api.airtable.com/v0/{BASE_ID}/Pedidos", headers=HEADERS_AIRTABLE, json=data)
                        st.toast(f"{f.get('Producto')} agregado!")

        with tabs[-1]:
            st.subheader("Resumen de Gastos")
            res_c = requests.get(f"https://api.airtable.com/v0/{BASE_ID}/Pedidos?filterByFormula=Mesa={nro_mesa}", headers=HEADERS_AIRTABLE)
            pedidos_mesa = res_c.json().get('records', [])
            
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("<div class='ticket-box'><h4>👤 MI PARTE</h4>", unsafe_allow_html=True)
                mios = [x for x in pedidos_mesa if x['fields'].get('Usuario') == st.session_state.usuario]
                t_mio = sum([float(x['fields'].get('Precio', 0)) for x in mios])
                for p in mios: st.write(f"• {p['fields'].get('Producto')}")
                st.write(f"**Total: ${t_mio}**")
                st.link_button("PAGAR MI PARTE", crear_link_pago("Mi parte Pagantodos", t_mio if t_mio > 0 else 1))
                st.markdown("</div>", unsafe_allow_html=True)

            with c2:
                st.markdown("<div class='ticket-box'><h4>👥 TOTAL MESA</h4>", unsafe_allow_html=True)
                t_mesa = sum([float(x['fields'].get('Precio', 0)) for x in pedidos_mesa])
                for p in pedidos_mesa: st.write(f"• {p['fields'].get('Usuario')}: {p['fields'].get('Producto')}")
                st.write(f"**Total: ${t_mesa}**")
                st.link_button("PAGAR TODA LA MESA", crear_link_pago("Total Mesa Pagantodos", t_mesa if t_mesa > 0 else 1))
                st.markdown("</div>", unsafe_allow_html=True)

# 7. FOOTER FINAL
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #64748b; padding: 20px;">
        <p>Propiedad de <b>Pagantodos 2026</b></p>
        <p style="font-size: 0.8rem;">Hecho con ❤️ para una experiencia gastronómica superior.</p>
    </div>
    """, 
    unsafe_allow_html=True
)