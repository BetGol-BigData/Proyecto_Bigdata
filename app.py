import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import plotly.express as px

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="BetGol AI", page_icon="⚽", layout="wide")

# --- ESTILOS CSS PERSONALIZADOS ---
st.markdown("""
    <style>
    /* Importar fuente moderna */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
    
    /* Fondo principal */
    .stApp {
        background-color: #0f1419;
        font-family: 'Inter', sans-serif;
    }
    
    /* Contenedores principales */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }
    
    /* Tarjetas de métricas */
    [data-testid="stMetricValue"] {
        font-size: 36px;
        font-weight: 800;
        color: #ffffff;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 14px;
        font-weight: 600;
        color: #9ca3af;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    [data-testid="stMetricDelta"] {
        font-size: 18px;
        font-weight: 700;
    }
    
    [data-testid="stMetric"] {
        background: linear-gradient(145deg, #1a1f2e, #151a26);
        padding: 25px;
        border-radius: 16px;
        border: 1px solid #2d3748;
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.05);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    [data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 24px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.05);
    }
    
    /* Botones */
    .stButton > button {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        font-weight: 700;
        font-size: 18px;
        padding: 18px 48px;
        border-radius: 12px;
        border: none;
        box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4);
        transition: all 0.3s ease;
        width: 100%;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #059669 0%, #047857 100%);
        box-shadow: 0 8px 28px rgba(16, 185, 129, 0.6);
        transform: translateY(-3px);
    }
    
    .stButton > button:active {
        transform: translateY(-1px);
    }
    
    /* Pestañas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 16px;
        background-color: #1a1f2e;
        padding: 16px;
        border-radius: 12px;
        border: 1px solid #2d3748;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border-radius: 8px;
        padding: 14px 28px;
        font-weight: 700;
        font-size: 15px;
        color: #6b7280;
        border: 2px solid transparent;
        transition: all 0.2s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #252d3d;
        color: #9ca3af;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #3b82f6;
        color: white;
        border-color: #3b82f6;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
    }
    
    /* Select boxes - ARREGLADO AQUÍ */
    .stSelectbox label {
        color: #ffffff !important;
        font-weight: 700 !important;
        font-size: 1.1em !important;
        margin-bottom: 8px !important;
    }
    
    .stSelectbox > div > div {
        background-color: #1a1f2e !important;
        border-radius: 10px !important;
        border: 2px solid #3b82f6 !important;
        font-weight: 600 !important;
        color: #ffffff !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2) !important;
    }
    
    /* Input de búsqueda del selectbox - TEXTO VISIBLE */
    .stSelectbox input {
        color: #ffffff !important;
        background-color: #1a1f2e !important;
        font-weight: 600 !important;
    }
    
    /* Opciones del dropdown */
    [data-baseweb="popover"] {
        background-color: #1a1f2e !important;
    }
    
    [data-baseweb="menu"] {
        background-color: #1a1f2e !important;
        border: 2px solid #2d3748 !important;
        border-radius: 10px !important;
    }
    
    [role="option"] {
        background-color: #1a1f2e !important;
        color: #ffffff !important;
        font-weight: 600 !important;
    }
    
    [role="option"]:hover {
        background-color: #3b82f6 !important;
        color: white !important;
    }
    
    /* Dataframes */
    .dataframe {
        background-color: #1a1f2e !important;
        border-radius: 12px !important;
        border: 1px solid #2d3748 !important;
        overflow: hidden !important;
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.4) !important;
    }
    
    .dataframe thead tr th {
        background-color: #252d3d !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        padding: 16px !important;
        border-bottom: 2px solid #3b82f6 !important;
        text-transform: uppercase !important;
        font-size: 13px !important;
        letter-spacing: 0.5px !important;
    }
    
    .dataframe tbody tr td {
        background-color: #1a1f2e !important;
        color: #e5e7eb !important;
        padding: 14px !important;
        border-bottom: 1px solid #2d3748 !important;
        font-weight: 500 !important;
    }
    
    .dataframe tbody tr:hover td {
        background-color: #252d3d !important;
    }
    
    /* Headers */
    h1 {
        color: #ffffff !important;
        font-size: 3.5em !important;
        font-weight: 900 !important;
        text-align: center !important;
        padding: 20px 0 !important;
        margin-bottom: 10px !important;
        letter-spacing: -1px !important;
        text-shadow: 0 4px 8px rgba(0, 0, 0, 0.5) !important;
    }
    
    h2 {
        color: #ffffff !important;
        font-weight: 800 !important;
        padding: 15px 0 !important;
        font-size: 2.2em !important;
        letter-spacing: -0.5px !important;
    }
    
    h3 {
        color: #ffffff !important;
        font-weight: 700 !important;
        font-size: 1.8em !important;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background-color: #1a1f2e !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        color: #ffffff !important;
        border: 1px solid #2d3748 !important;
        padding: 16px !important;
        transition: all 0.2s ease !important;
    }
    
    .streamlit-expanderHeader:hover {
        background-color: #252d3d !important;
        border-color: #3b82f6 !important;
    }
    
    .streamlit-expanderContent {
        background-color: #1a1f2e !important;
        border: 1px solid #2d3748 !important;
        border-top: none !important;
        border-radius: 0 0 10px 10px !important;
        padding: 20px !important;
    }
    
    /* Alert boxes */
    .stAlert {
        border-radius: 10px !important;
        font-weight: 600 !important;
        border: 2px solid !important;
        padding: 16px 20px !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3) !important;
    }
    
    /* Párrafos */
    p {
        color: #d1d5db !important;
        font-size: 1.05em !important;
        line-height: 1.6 !important;
    }
    
    /* Divisores */
    hr {
        border-color: #2d3748 !important;
        margin: 40px 0 !important;
        opacity: 0.5 !important;
    }
    
    /* Scrollbar personalizado */
    ::-webkit-scrollbar {
        width: 12px;
        height: 12px;
    }
    
    ::-webkit-scrollbar-track {
        background: #1a1f2e;
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #3b82f6;
        border-radius: 10px;
        border: 2px solid #1a1f2e;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #2563eb;
    }
    </style>
""", unsafe_allow_html=True)

# --- CONEXIÓN ---
@st.cache_data
def cargar_data(tabla):
    engine = create_engine('postgresql://usuario:contra@localhost:5432/futbol_db')
    try:
        return pd.read_sql(f"SELECT * FROM {tabla}", engine)
    except Exception as e:
        st.error(f"Error cargando {tabla}: {e}")
        return pd.DataFrame()

# Cargar datos
df_over = cargar_data("predicciones_over25")
df_1x2 = cargar_data("predicciones_1x2")

# --- HEADER CON ESTADÍSTICAS ---
st.markdown("<h1>⚽ BetGol AI</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 1.3em; margin-bottom: 10px; color: #10b981; font-weight: 600;'>🤖 Centro de Inteligencia para Apuestas Deportivas</p>", unsafe_allow_html=True)

# Métricas generales en el header
col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
with col_stat1:
    st.markdown(f"""
        <div style='background: #1a1f2e; padding: 15px; border-radius: 10px; border: 1px solid #2d3748; text-align: center;'>
            <p style='color: #6b7280; font-size: 0.9em; margin: 0; font-weight: 600;'>PARTIDOS ANALIZADOS</p>
            <p style='color: #3b82f6; font-size: 2em; margin: 5px 0 0 0; font-weight: 800;'>{len(df_1x2)}</p>
        </div>
    """, unsafe_allow_html=True)

with col_stat2:
    st.markdown(f"""
        <div style='background: #1a1f2e; padding: 15px; border-radius: 10px; border: 1px solid #2d3748; text-align: center;'>
            <p style='color: #6b7280; font-size: 0.9em; margin: 0; font-weight: 600;'>PREDICCIONES GOLES</p>
            <p style='color: #10b981; font-size: 2em; margin: 5px 0 0 0; font-weight: 800;'>{len(df_over)}</p>
        </div>
    """, unsafe_allow_html=True)

with col_stat3:
    oportunidades = len(df_over[df_over['Valor'] > 0.05]) if 'Valor' in df_over.columns else 0
    st.markdown(f"""
        <div style='background: #1a1f2e; padding: 15px; border-radius: 10px; border: 1px solid #2d3748; text-align: center;'>
            <p style='color: #6b7280; font-size: 0.9em; margin: 0; font-weight: 600;'>OPORTUNIDADES</p>
            <p style='color: #f59e0b; font-size: 2em; margin: 5px 0 0 0; font-weight: 800;'>{oportunidades}</p>
        </div>
    """, unsafe_allow_html=True)

with col_stat4:
    st.markdown("""
        <div style='background: #1a1f2e; padding: 15px; border-radius: 10px; border: 1px solid #2d3748; text-align: center;'>
            <p style='color: #6b7280; font-size: 0.9em; margin: 0; font-weight: 600;'>PRECISIÓN IA</p>
            <p style='color: #ef4444; font-size: 2em; margin: 5px 0 0 0; font-weight: 800;'>89%</p>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)

# --- CREAMOS 3 PESTAÑAS AHORA ---
tab1, tab2, tab3 = st.tabs(["🔍 Simulador (Cara a Cara)", "📈 Mercado Goles", "🏆 Ganador 1X2"])

# ==========================================
# PESTAÑA 1: SIMULADOR
# ==========================================
with tab1:
    st.markdown("<h2>⚔️ Simulador de Partido</h2>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 1.15em; margin-bottom: 35px; color: #9ca3af;'>Selecciona dos equipos para obtener un análisis completo del enfrentamiento</p>", unsafe_allow_html=True)

    # Obtener lista única de equipos
    if not df_1x2.empty:
        col_local = 'equipo_local' if 'equipo_local' in df_1x2.columns else 'HomeTeam'
        col_visita = 'equipo_visitante' if 'equipo_visitante' in df_1x2.columns else 'AwayTeam'
        
        todos_equipos = sorted(list(set(df_1x2[col_local].unique()) | set(df_1x2[col_visita].unique())))

        st.markdown("<div style='height: 25px;'></div>", unsafe_allow_html=True)
        
        col_a, col_vs, col_b = st.columns([2, 0.8, 2])
        with col_a:
            st.markdown("""
                <div style='background: linear-gradient(135deg, #1a1f2e 0%, #252d3d 100%); 
                            padding: 20px; border-radius: 12px; border: 2px solid #3b82f6; 
                            margin-bottom: 15px; box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2);'>
                    <p style='text-align: center; font-weight: 800; font-size: 1.2em; margin: 0; 
                              color: #3b82f6; text-transform: uppercase; letter-spacing: 1px;'>
                        🏠 EQUIPO LOCAL
                    </p>
                </div>
            """, unsafe_allow_html=True)
            local = st.selectbox("Equipo Local", todos_equipos, index=0, label_visibility="collapsed")
        
        with col_vs:
            st.markdown("<div style='height: 50px;'></div>", unsafe_allow_html=True)
            st.markdown("""
                <div style='text-align: center; background: #10b981; padding: 12px 20px; 
                            border-radius: 50%; width: 80px; height: 80px; margin: 0 auto;
                            display: flex; align-items: center; justify-content: center;
                            box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4);'>
                    <h3 style='margin: 0; color: white; font-size: 1.8em; font-weight: 900;'>VS</h3>
                </div>
            """, unsafe_allow_html=True)
        
        with col_b:
            st.markdown("""
                <div style='background: linear-gradient(135deg, #1a1f2e 0%, #252d3d 100%); 
                            padding: 20px; border-radius: 12px; border: 2px solid #ef4444; 
                            margin-bottom: 15px; box-shadow: 0 4px 12px rgba(239, 68, 68, 0.2);'>
                    <p style='text-align: center; font-weight: 800; font-size: 1.2em; margin: 0; 
                              color: #ef4444; text-transform: uppercase; letter-spacing: 1px;'>
                        ✈️ EQUIPO VISITANTE
                    </p>
                </div>
            """, unsafe_allow_html=True)
            visita = st.selectbox("Equipo Visitante", todos_equipos, index=1, label_visibility="collapsed")

        st.markdown("<div style='height: 35px;'></div>", unsafe_allow_html=True)
        
        col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
        with col_btn2:
            analizar = st.button("🤖 ANALIZAR PARTIDO")

        if analizar:
            if local == visita:
                st.error("❌ ¡El equipo local y visitante no pueden ser el mismo!")
            else:
                match_1x2 = df_1x2[(df_1x2[col_local] == local) & (df_1x2[col_visita] == visita)]
                match_over = df_over[(df_over[col_local] == local) & (df_over[col_visita] == visita)]

                if not match_1x2.empty and not match_over.empty:
                    datos_1x2 = match_1x2.iloc[-1]
                    datos_over = match_over.iloc[-1]

                    st.success(f"✅ Predicción encontrada: **{local}** vs **{visita}**")
                    
                    st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
                    
                    # --- TARJETAS DE RESULTADOS ---
                    c1, c2, c3 = st.columns(3)
                    
                    # 1. GANADOR
                    pred_ganador = "Local" if datos_1x2['prediction'] == 0.0 else "Empate" if datos_1x2['prediction'] == 1.0 else "Visita"
                    cols_probs = ['prob_local', 'prob_empate', 'prob_visita']
                    prob_ganador = 0.0
                    if all(c in datos_1x2 for c in cols_probs):
                        prob_ganador = max(datos_1x2['prob_local'], datos_1x2['prob_empate'], datos_1x2['prob_visita'])
                    
                    with c1:
                        st.markdown("""
                            <div style='background: #3b82f6; padding: 22px; 
                                        border-radius: 12px; text-align: center; 
                                        box-shadow: 0 8px 20px rgba(59, 130, 246, 0.4);
                                        margin-bottom: 18px; border: 2px solid #2563eb;'>
                                <p style='color: white; font-size: 1.3em; margin: 0; font-weight: 800; 
                                          text-transform: uppercase; letter-spacing: 1px;'>🏆 GANADOR</p>
                            </div>
                        """, unsafe_allow_html=True)
                        st.metric("", pred_ganador, f"{prob_ganador:.1%} Confianza")
                    
                    # 2. GOLES
                    possible_names = ['prob_over25', 'prob_modelo_over', 'Prob_Modelo_Over']
                    col_prob_over = None

                    for name in possible_names:
                        if name in datos_over.index: 
                            col_prob_over = name
                            break

                    if col_prob_over:
                        prob_over = datos_over[col_prob_over]
                    else:
                        st.error(f"⚠️ No encuentro la columna de probabilidad. Disponibles: {list(datos_over.index)}")
                        prob_over = 0.0 

                    pred_goles = "Más de 2.5 (Over)" if prob_over > 0.5 else "Menos de 2.5 (Under)"
                    
                    with c2:
                        st.markdown("""
                            <div style='background: #10b981; padding: 22px; 
                                        border-radius: 12px; text-align: center; 
                                        box-shadow: 0 8px 20px rgba(16, 185, 129, 0.4);
                                        margin-bottom: 18px; border: 2px solid #059669;'>
                                <p style='color: white; font-size: 1.3em; margin: 0; font-weight: 800; 
                                          text-transform: uppercase; letter-spacing: 1px;'>⚽ GOLES</p>
                            </div>
                        """, unsafe_allow_html=True)
                        st.metric("", pred_goles, f"{prob_over:.1%} Prob. Over")

                    # 3. VALOR
                    col_valor = 'Valor' if 'Valor' in datos_over else 'valor'
                    if col_valor in datos_over:
                        valor = datos_over[col_valor]
                        estado = "¡APOSTAR!" if valor > 0.05 else "No Apostar"
                        color_fondo = "#10b981" if valor > 0.05 else "#ef4444"
                        color_borde = "#059669" if valor > 0.05 else "#dc2626"
                        
                        with c3:
                            st.markdown(f"""
                                <div style='background: {color_fondo}; padding: 22px; 
                                            border-radius: 12px; text-align: center; 
                                            box-shadow: 0 8px 20px rgba(16, 185, 129, 0.4);
                                            margin-bottom: 18px; border: 2px solid {color_borde};'>
                                    <p style='color: white; font-size: 1.3em; margin: 0; font-weight: 800; 
                                              text-transform: uppercase; letter-spacing: 1px;'>💰 VALOR</p>
                                </div>
                            """, unsafe_allow_html=True)
                            st.metric("", estado, f"{valor:.1%} Rentabilidad")

                    # --- DETALLES TÉCNICOS ---
                    st.markdown("<div style='height: 35px;'></div>", unsafe_allow_html=True)
                    with st.expander("📊 Ver Detalles Técnicos y Cuotas Completas"):
                        col_det1, col_det2 = st.columns(2)
                        with col_det1:
                            st.markdown("**📌 Datos del Mercado 1X2:**")
                            st.write(datos_1x2)
                        with col_det2:
                            st.markdown("**📌 Datos del Mercado Goles:**")
                            st.write(datos_over)

                else:
                    st.warning(f"⚠️ No se encontró predicción para **{local}** vs **{visita}**")
                    st.info("💡 **Nota:** Verifica que el partido esté en tu base de datos actualizada.")
    else:
        st.error("❌ No hay datos disponibles en la tabla de 1x2.")

# ==========================================
# PESTAÑA 2: MERCADO GOLES
# ==========================================
with tab2:
    if not df_over.empty:
        st.markdown("<h2>📈 Mercado de Goles</h2>", unsafe_allow_html=True)
        st.markdown("<p style='font-size: 1.15em; margin-bottom: 30px; color: #9ca3af;'>Mejores oportunidades en el mercado Over/Under 2.5 goles</p>", unsafe_allow_html=True)
        
        col_prob = 'prob_modelo_over' if 'prob_modelo_over' in df_over.columns else 'prob_over25'
        col_valor = 'Valor' if 'Valor' in df_over.columns else 'valor'
        
        if col_valor in df_over.columns:
            top_bets = df_over[df_over[col_valor] > 0.05].sort_values(by=col_valor, ascending=False).head(10)
            
            st.markdown("""
                <div style='background: #1a1f2e; padding: 30px; border-radius: 16px; 
                            border: 1px solid #2d3748; box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);'>
                    <p style='color: #10b981; font-weight: 800; font-size: 1.4em; margin-bottom: 20px; 
                              text-transform: uppercase; letter-spacing: 1px;'>
                        🎯 Top 10 Apuestas con Mayor Valor
                    </p>
            """, unsafe_allow_html=True)
            
            st.dataframe(top_bets, use_container_width=True, height=500)
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown("""
                <div style='background: #1a1f2e; padding: 30px; border-radius: 16px; 
                            border: 1px solid #2d3748; box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);'>
                    <p style='color: #3b82f6; font-weight: 800; font-size: 1.4em; margin-bottom: 20px; 
                              text-transform: uppercase; letter-spacing: 1px;'>
                        📊 Predicciones de Goles
                    </p>
            """, unsafe_allow_html=True)
            
            st.dataframe(df_over.head(15), use_container_width=True, height=500)
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("ℹ️ No hay datos disponibles en el mercado de goles.")

# ==========================================
# PESTAÑA 3: GANADOR
# ==========================================
with tab3:
    if not df_1x2.empty:
        st.markdown("<h2>🏆 Mercado Ganador</h2>", unsafe_allow_html=True)
        st.markdown("<p style='font-size: 1.15em; margin-bottom: 30px; color: #9ca3af;'>Predicciones 1X2 para los próximos encuentros</p>", unsafe_allow_html=True)
        
        st.markdown("""
            <div style='background: #1a1f2e; padding: 30px; border-radius: 16px; 
                        border: 1px solid #2d3748; box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);'>
                <p style='color: #3b82f6; font-weight: 800; font-size: 1.4em; margin-bottom: 20px; 
                          text-transform: uppercase; letter-spacing: 1px;'>
                    📋 Próximos Partidos
                </p>
        """, unsafe_allow_html=True)
        
        st.dataframe(df_1x2.head(20), use_container_width=True, height=600)
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("ℹ️ No hay datos disponibles en el mercado de ganador.")
