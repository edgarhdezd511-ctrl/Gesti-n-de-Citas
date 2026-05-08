import streamlit as st
import psycopg2
import pandas as pd
import os
from datetime import datetime

# 1. Configuración de conexión (Railway)
DATABASE_URL = os.getenv("DATABASE_URL")

def init_db():
    if not DATABASE_URL:
        return
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cur = conn.cursor()
        # Crear tabla con todos los campos solicitados
        cur.execute("""
            CREATE TABLE IF NOT EXISTS citas (
                id SERIAL PRIMARY KEY,
                no_proveedor TEXT,
                razon_social TEXT,
                cedis_origen_num TEXT,
                cedis_origen_siglas TEXT,
                cedis_destino_num TEXT,
                cedis_destino_siglas TEXT,
                pedido NUMERIC,
                sku TEXT,
                descripcion TEXT,
                unidades_facturadas INTEGER,
                rampa TEXT,
                fecha_entrega DATE,
                hora_entrega TEXT,
                folio_cita TEXT,
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        st.error(f"Error al inicializar base de datos: {e}")

init_db()

# --- CONFIGURACIÓN VISUAL ---
st.set_page_config(page_title="Portal de Citas | Coppel", layout="wide", page_icon="🚚")

# Estilo CSS para botones y colores corporativos
st.markdown("""
    <style>
    .stButton>button {
        background-color: #0056b3;
        color: white;
        border-radius: 8px;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #fecb00;
        color: #0056b3;
    }
    </style>
    """, unsafe_allow_html=True)

# Encabezado
col_logo, col_titulo = st.columns([1, 4])
with col_logo:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/2/2a/Coppel.svg/1200px-Coppel.svg.png", width=160)
with col_titulo:
    st.title("Sistema de Gestión de Citas CEDIS")
    st.subheader("Portal Oficial de Proveedores - Coppel")

st.markdown("---")

# --- FORMULARIO DE REGISTRO ---
with st.form("form_citas", clear_on_submit=True):
    st.info("Complete todos los campos para programar su entrega en el CEDIS correspondiente.")
    
    # Fila 1: Datos del Proveedor
    c1, c2, c3 = st.columns(3)
    with c1:
        no_prov = st.text_input("No. PROVEEDOR")
    with c2:
        razon = st.text_input("RAZÓN SOCIAL")
    with c3:
        pedido = st.text_input("PEDIDO ($)")

    # Fila 2: Logística
    st.markdown("**📍 Ruta y Destino**")
    c4, c5, c6, c7 = st.columns(4)
    with c4:
        c_orig_n = st.text_input("NUM. CEDIS ORIGEN")
    with c5:
        c_orig_s = st.selectbox("CEDIS ORIGEN", ["GDLJ", "CDMX", "MTY", "CUL", "MER"])
    with c6:
        c_dest_n = st.text_input("NUM. CEDIS DESTINO")
    with c7:
        c_dest_s = st.selectbox("CEDIS DESTINO", ["GDLJ", "CDMX", "MTY", "CUL", "MER"])

    # Fila 3: Mercancía
    st.markdown("**📦 Información de Carga**")
    c8, c9, c10 = st.columns(3)
    with c8:
        sku = st.text_input("SKU / Código")
    with c9:
        desc = st.text_input("DESCRIPCIÓN")
    with c10:
        unidades = st.number_input("UNIDADES FACTURADAS", min_value=1, step=1)

    # Fila 4: Cita
    st.markdown("**⏰ Horario y Rampa**")
    c11, c12, c13 = st.columns(3)
    with c11:
        fecha = st.date_input("FECHA DE ENTREGA", min_value=datetime.today())
    with c12:
        rampa = st.text_input("RAMPA ASIGNADA")
    with c13:
        hora = st.time_input("HORA DE CITA")

    enviado = st.form_submit_button("📩 REGISTRAR CITA Y GENERAR FOLIO")

    if enviado:
        if no_prov and razon and sku:
            # Generar Folio (Ej: GDLJ_1205)
            folio_generado = f"{c_dest_s}_{datetime.now().strftime('%M%S')}"
            
            try:
                conn = psycopg2.connect(DATABASE_URL, sslmode='require')
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO citas (
                        no_proveedor, razon_social, cedis_origen_num, cedis_origen_siglas, 
                        cedis_destino_num, cedis_destino_siglas, pedido, sku, descripcion, 
                        unidades_facturadas, rampa, fecha_entrega, hora_entrega, folio_cita
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (no_prov, razon, c_orig_n, c_orig_s, c_dest_n, c_dest_s, pedido, 
                      sku, desc, int(unidades), rampa, fecha, str(hora), folio_generado))
                conn.commit()
                cur.close()
                conn.close()
                st.success(f"✅ ¡Cita registrada! Su folio es: **{folio_generado}**")
                st.balloons()
            except Exception as e:
                st.error(f"Error al guardar: {e}")
        else:
            st.warning("⚠️ Favor de llenar los campos obligatorios (Proveedor, Razón Social y SKU)")

# --- PANEL DE DESCARGA (ADMIN) ---
st.markdown("<br><br>", unsafe_allow_html=True)
with st.expander("🛠️ PANEL DE ADMINISTRACIÓN (Solo personal autorizado)"):
    st.write("Presione el botón para ver la tabla actualizada y descargar el reporte.")
    if st.button("📊 CONSULTAR BASE DE DATOS"):
        try:
            conn = psycopg2.connect(DATABASE_URL, sslmode='require')
            query = "SELECT * FROM citas ORDER BY fecha_registro DESC"
            df = pd.read_sql_query(query, conn)
            conn.close()

            if not df.empty:
                st.dataframe(df)
                
                # Convertir a CSV para descarga
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 DESCARGAR EXCEL (CSV)",
                    data=csv,
                    file_name=f"reporte_citas_coppel_{datetime.now().strftime('%d_%m_%Y')}.csv",
                    mime='text/csv',
                )
            else:
                st.info("No hay registros disponibles para mostrar.")
        except Exception as e:
            st.error(f"Error al leer la base de datos: {e}")
