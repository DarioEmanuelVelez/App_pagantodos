import requests

# Reemplaza la línea 4
# ASÍ DEBE QUEDAR EL CÓDIGO (NO PONGAS TUS TOKENS ACÁ)
TOKEN_AIRTABLE = st.secrets.get("AIRTABLE_TOKEN", "")
BASE_ID = st.secrets.get("AIRTABLE_BASE_ID", "")
MP_TOKEN = st.secrets.get("MP_ACCESS_TOKEN", None)
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

# 1. IDENTIDAD
print("--- BIENVENIDO A LA CAPKE ---")
nombre_usuario = input("Tu nombre: ")
mesa = 5

# 2. CARGAR MENÚ (Lo hacemos una sola vez al principio)
res_menu = requests.get(f"https://api.airtable.com/v0/{BASE_ID}/Menu", headers=HEADERS)
menu_items = res_menu.json().get('records', [])

# --- PASO NUEVO: EL BUCLE DE PEDIDOS ---
pedidos_del_momento = []
continuar = "si"

while continuar.lower() == "si":
    print("\n--- MENÚ ---")
    for i, item in enumerate(menu_items):
        print(f"{i + 1}. {item['fields'].get('Producto')} - ${item['fields'].get('Precio')}")
    
    seleccion = int(input("\n¿Qué vas a pedir? (Nro): "))
    producto = menu_items[seleccion - 1]['fields']
    
    # Guardamos en nuestra lista local
    pedidos_del_momento.append(producto)
    print(f"✅ Agregado: {producto.get('Producto')}")
    
    continuar = input("¿Querés pedir algo más? (si/no): ")

# 3. ENVIAR TODO A AIRTABLE
print("\nEnviando pedidos a la cocina...")
for pedido in pedidos_del_momento:
    datos = {
        "records": [{
            "fields": {
                "Usuario": nombre_usuario,
                "Producto": pedido.get('Producto'),
                "Precio": pedido.get('Precio'),
                "Mesa": mesa,
                "Estado": "Pendiente"
            }
        }]
    }
    requests.post(f"https://api.airtable.com/v0/{BASE_ID}/Pedidos", headers=HEADERS, json=datos)

# 4. CUENTA INDIVIDUAL
total = sum(p.get('Precio', 0) for p in pedidos_del_momento)
print(f"\n--- CUENTA FINAL DE {nombre_usuario.upper()} ---")
for p in pedidos_del_momento:
    print(f"- {p.get('Producto')}: ${p.get('Precio')}")
print(f"TOTAL A PAGAR: ${total}")

# # --- PASO 5: ELECCIÓN DE PAGO CON DETALLE ---
print("\n" + "="*40)
print("          FINALIZAR CUENTA")
print("="*40)
print("1. Pagar SOLAMENTE lo mío")
print("2. Pagar TODA la mesa")
eleccion = input("Elegí una opción (1 o 2): ")

monto_a_cobrar = 0

if eleccion == "1":
    # --- DETALLE INDIVIDUAL ---
    monto_a_cobrar = total
    print(f"\n--- TU TICKET DETALLADO ({nombre_usuario}) ---")
    for p in pedidos_del_momento:
        print(f"• {p.get('Producto'):.<25} ${p.get('Precio'):>7}")
    print("-" * 40)
    print(f"TOTAL A PAGAR: {'':.<15} ${monto_a_cobrar:>7}")

else:
    # --- DETALLE DE TODA LA MESA ---
    print(f"\nConsultando consumos de la Mesa {mesa}...")
    
    # Buscamos en Airtable todos los pendientes de la mesa
    formula = f"AND(Mesa={mesa}, Estado='Pendiente')"
    url_mesa = f"https://api.airtable.com/v0/{BASE_ID}/Pedidos?filterByFormula={formula}"
    res_mesa = requests.get(url_mesa, headers=HEADERS)
    todos_los_records = res_mesa.json().get('records', [])
    
    monto_a_cobrar = 0
    print(f"\n--- TICKET TOTAL MESA {mesa} ---")
    
    for item in todos_los_records:
        campos = item['fields']
        cliente = campos.get('Usuario')
        prod = campos.get('Producto')
        precio = campos.get('Precio', 0)
        
        monto_a_cobrar += precio
        # Mostramos quién pidió cada cosa
        print(f"[{cliente[:3].upper()}] {prod:.<22} ${precio:>7}")
    
    print("-" * 40)
    print(f"TOTAL GENERAL: {'':.<15} ${monto_a_cobrar:>7}")

# --- PASO 6: BOTÓN DE PAGO ---
print("\n" + "="*40)
confirmar = input(f"¿Confirmar pago de ${monto_a_cobrar}? (si/no): ")

if confirmar.lower() == "si":
    link_de_pago = f"https://www.mercadopago.com.ar/checkout/v1/redirect?pref_id=MESA{mesa}_{monto_a_cobrar}"
    print(f"\n✅ Link generado. Pagá aquí: {link_de_pago}")
    # En un celu, acá se abriría el navegador
else:
    print("\nOperación cancelada. Podés seguir pidiendo o revisar luego.")