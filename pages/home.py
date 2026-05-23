"""
home.py — Pantalla principal de Rake
Selección de tipo de cálculo de intereses moratorios.
"""
import streamlit as st

st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
st.title("⚖️ Intereses Moratorios")
st.caption("Doctrina RASTRILLA · VEGA — Cámara Federal de Apelaciones de Mendoza")
st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3, gap="large")

with col1:
    st.markdown("""
<div class="calc-card">
  <span class="calc-card-icon">📋</span>
  <div class="calc-card-title">Ejecución de Sentencia</div>
  <div class="calc-card-desc">
    Cálculo de 120 días hábiles judiciales.<br>
    División automática Tramo A / Tramo B.<br>
    Tasa pasiva BCRA desde el día 121.
  </div>
  <span class="calc-card-badge">Próximamente</span>
</div>
""", unsafe_allow_html=True)

with col2:
    st.markdown("""
<div class="calc-card">
  <span class="calc-card-icon">📎</span>
  <div class="calc-card-title">Ampliación de Ejecución</div>
  <div class="calc-card-desc">
    Mora desde el 1° del mes siguiente<br>
    por cada período de la planilla.<br>
    Tasa pasiva BCRA.
  </div>
</div>
""", unsafe_allow_html=True)
    st.markdown("<div style='height:0.25rem'></div>", unsafe_allow_html=True)
    if st.button("▶ Iniciar", key="btn_ampliacion", use_container_width=True, type="primary"):
        st.switch_page("pages/ampliacion.py")

with col3:
    st.markdown("""
<div class="calc-card">
  <span class="calc-card-icon">💰</span>
  <div class="calc-card-title">Intereses Aprobados hasta Cobro</div>
  <div class="calc-card-desc">
    Capital único aprobado judicialmente.<br>
    Intereses desde el día siguiente a la<br>
    aprobación hasta el efectivo cobro.
  </div>
</div>
""", unsafe_allow_html=True)
    st.markdown("<div style='height:0.25rem'></div>", unsafe_allow_html=True)
    if st.button("▶ Iniciar", key="btn_cobro", use_container_width=True, type="primary"):
        st.switch_page("pages/intereses_cobro.py")
