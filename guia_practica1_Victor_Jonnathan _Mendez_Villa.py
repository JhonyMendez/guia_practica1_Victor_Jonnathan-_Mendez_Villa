import requests
import pandas as pd
import plotly.express as px
import streamlit as st
import time

st.set_page_config(
    page_title="Análisis de Compras Públicas Ecuador",
    layout="wide",
    page_icon="📊"
)

st.title("📊 Análisis de Datos de Compras Públicas en Ecuador")
st.markdown("""
**Autor:** Victor Jonnathan Méndez Villa  
**Asignatura:** Inteligencia Artificial  
**Tema:** Análisis de Datos con Python  
**Docente:** Mgtr. Verónica Paulina Chimbo Coronel
""")

st.sidebar.header("⚙️ Parámetros de consulta")

# Checkbox para analizar todos los años
analizar_todos_anos = st.sidebar.checkbox(
    "📅 Analizar todos los años (2015-2025)", 
    value=False,
    help="Selecciona esta opción para analizar datos de todos los años disponibles"
)

# Selector de año individual (se deshabilita si se marca el checkbox)
if analizar_todos_anos:
    years = list(range(2015, 2026))  # 2015 a 2025
    st.sidebar.info(f"✅ Analizando {len(years)} años: 2015-2025")
    year = None  # No se usa un año específico
else:
    year = st.sidebar.selectbox("Selecciona el año", [2025, 2024, 2023, 2022, 2021, 2020, 2019, 2018, 2017, 2016, 2015])
    years = [year]

region = st.sidebar.selectbox(
    "Provincia", 
    ["TODAS", "Pichincha", "Guayas", "Azuay", "Manabí", "El Oro", 
     "Tungurahua", "Los Ríos", "Imbabura", "Chimborazo", "Cotopaxi",
     "Loja", "Esmeraldas", "Santo Domingo", "Santa Elena", "Bolívar",
     "Cañar", "Carchi", "Pastaza", "Morona Santiago", "Napo",
     "Zamora Chinchipe", "Sucumbíos", "Orellana", "Galápagos"],
    help="Selecciona una provincia específica o TODAS para consultar todo el país"
)

tipo_contratacion = st.sidebar.selectbox(
    "Tipo de contratación", 
    ["TODAS", "Bienes", "Obras", "Servicios", "Consultoría", "Licitación", 
     "Menor Cuantía", "Ínfima Cuantía", "Subasta", "Catálogo"],
    help="Selecciona un tipo específico o TODAS para todos los tipos de contratación"
)

if st.sidebar.button("🔍 Cargar datos"):
    if tipo_contratacion != "TODAS":
        search_term = tipo_contratacion
    else:
        search_term = "proceso"  
    
    # Construcción de filtros activos
    if analizar_todos_anos:
        filtros_activos = f"**Filtros aplicados:** Años 2015-2025"
    else:
        filtros_activos = f"**Filtros aplicados:** Año {year}"
    
    if region != "TODAS":
        filtros_activos += f" | Provincia: {region}"
    else:
        filtros_activos += " | Provincia: TODAS"
    if tipo_contratacion != "TODAS":
        filtros_activos += f" | Tipo: {tipo_contratacion}"
    else:
        filtros_activos += " | Tipo: TODAS"
    
    st.info(filtros_activos)
    
    if analizar_todos_anos:
        st.warning(f"⚠️ Analizando {len(years)} años. Este proceso puede tardar bastante tiempo (varios minutos).")
    else:
        st.info("Cargando datos desde la API oficial... esto puede tardar varios minutos")

    url = "https://datosabiertos.compraspublicas.gob.ec/PLATAFORMA/api/search_ocds"
    
    all_data = []
    
    # Iteración por cada año
    for year_idx, current_year in enumerate(years):
        st.subheader(f"📥 Descargando datos del año {current_year}...")
        
        page = 1
        max_consecutive_empty = 3  
        empty_pages = 0
        year_data = []
        
        progress_placeholder = st.empty()
        status_text = st.empty()
        
        while True:
            params = {
                "year": current_year,
                "search": search_term,
                "page": page
            }
            
            if region != "TODAS":
                params["buyer"] = region
            
            try:
                status_text.text(f"Año {current_year} - Página {page}... ({len(year_data)} registros)")
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                if "data" in data and len(data["data"]) > 0:
                    year_data.extend(data["data"])
                    empty_pages = 0  
                    
                    total_pages = data.get("pages", "?")
                    progress_placeholder.info(f"📊 Año {current_year} - Página {page} de {total_pages} | Registros: {len(year_data)}")
                    
                    if page >= data.get("pages", page):
                        status_text.success(f"✅ Año {current_year} completado ({len(year_data)} registros)")
                        break
                        
                    page += 1
                    time.sleep(0.3)  
                else:
                    empty_pages += 1
                    if empty_pages >= max_consecutive_empty:
                        status_text.warning(f"⚠️ No hay más datos para el año {current_year}")
                        break
                    page += 1
                    
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Error de conexión en año {current_year}, página {page}: {e}")
                break
            except Exception as e:
                st.error(f"❌ Error al procesar datos del año {current_year}, página {page}: {e}")
                break
        
        all_data.extend(year_data)
        progress_placeholder.empty()
        status_text.empty()
        
        st.success(f"✅ Año {current_year}: {len(year_data)} registros obtenidos")
    
    if not all_data:
        st.error("❌ No se encontraron datos con los filtros aplicados")
        st.stop()
    
    df = pd.DataFrame(all_data)
    
    if analizar_todos_anos:
        st.success(f"✅ Datos cargados correctamente - {len(df)} registros obtenidos de {len(years)} años")
    else:
        st.success(f"✅ Datos cargados correctamente - {len(df)} registros obtenidos")
    
    # Obtención de montos
    st.info("🔍 Obteniendo montos de contratos... esto puede tardar unos minutos")
    
    montos_data = []
    progress_bar = st.progress(0)
    status_monto = st.empty()
    
    max_ocids = min(len(df), 500)
    
    for idx, ocid in enumerate(df['ocid'].head(max_ocids)):
        try:
            status_monto.text(f"Consultando monto {idx + 1} de {max_ocids}...")
            record_url = "https://datosabiertos.compraspublicas.gob.ec/PLATAFORMA/api/record"
            response = requests.get(record_url, params={"ocid": ocid}, timeout=15)
            
            if response.status_code == 200:
                record_data = response.json()
                
                if "records" in record_data and len(record_data["records"]) > 0:
                    releases = record_data["records"][0].get("releases", [])
                    if releases:
                        release = releases[0]
                        
                        contracts = release.get("contracts", [])
                        monto = 0
                        num_contracts = 0
                        
                        for contract in contracts:
                            if "value" in contract and "amount" in contract["value"]:
                                monto += float(contract["value"]["amount"])
                                num_contracts += 1
                        
                        if monto == 0:
                            awards = release.get("awards", [])
                            for award in awards:
                                if "value" in award and "amount" in award["value"]:
                                    monto += float(award["value"]["amount"])
                        
                        montos_data.append({
                            "ocid": ocid,
                            "monto_total": monto,
                            "num_contratos": num_contracts if num_contracts > 0 else 1
                        })
            
            progress_bar.progress((idx + 1) / max_ocids)
            time.sleep(0.2) 
            
        except Exception as e:
            continue
    
    progress_bar.empty()
    status_monto.empty()
    
    if montos_data:
        df_montos = pd.DataFrame(montos_data)
        df = df.merge(df_montos, on="ocid", how="left")
        df["monto_total"] = df["monto_total"].fillna(0)
        df["num_contratos"] = df["num_contratos"].fillna(0)
        st.success(f"✅ Montos obtenidos para {len(montos_data)} registros")
    else:
        df["monto_total"] = 0
        df["num_contratos"] = 0
        st.warning("⚠️ No se pudieron obtener montos para estos registros")

    st.subheader("🧹 Limpieza de datos")

    rename_map = {
        "buyerName": "entidad_compradora",
        "internal_type": "tipo_contratacion",
        "single_provider": "proveedor"
    }
    df = df.rename(columns=rename_map)

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df["year"] = df["date"].dt.year
        df["month"] = df["date"].dt.month
        df["month_name"] = df["date"].dt.strftime('%B')

    df = df.drop_duplicates(subset=["ocid"], keep="first")

    st.write("**Vista previa de datos limpios:**")
    st.dataframe(df.head(10))

    col_info1, col_info2 = st.columns(2)
    with col_info1:
        st.write(f"**Dimensiones:** {df.shape[0]} filas × {df.shape[1]} columnas")
    with col_info2:
        st.write(f"**Columnas disponibles:** {', '.join(df.columns[:5])}...")

    st.subheader("📈 Análisis Descriptivo")

    total_registros = len(df)
    monto_total = df["monto_total"].sum()
    promedio = df["monto_total"].mean()
    total_contratos = df["num_contratos"].sum()
    tipos_unicos = df["tipo_contratacion"].nunique() if "tipo_contratacion" in df.columns else 0
    entidades_unicas = df["entidad_compradora"].nunique() if "entidad_compradora" in df.columns else 0
    proveedores_unicos = df["proveedor"].nunique() if "proveedor" in df.columns else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total de registros", f"{total_registros:,}")
    col2.metric("Monto total", f"${monto_total:,.2f}")
    col3.metric("Promedio por registro", f"${promedio:,.2f}")
    col4.metric("Contratos (suma)", f"{int(total_contratos):,}")
    
    col5, col6, col7 = st.columns(3)
    col5.metric("Tipos de contratación", f"{tipos_unicos}")
    col6.metric("Entidades compradoras", f"{entidades_unicas}")
    col7.metric("Proveedores únicos", f"{proveedores_unicos}")

    st.subheader("📊 Visualizaciones")

    # Visualización específica para análisis multi-año
    if analizar_todos_anos and "year" in df.columns:
        year_stats = df.groupby("year").agg({
            "ocid": "count",
            "monto_total": "sum"
        }).reset_index()
        year_stats.columns = ["year", "cantidad", "monto_total"]
        
        fig_year = px.bar(year_stats, x="year", y="cantidad",
                          title="📅 Evolución Anual de Procesos de Contratación (2015-2025)",
                          text_auto=True,
                          labels={"cantidad": "Cantidad de Procesos", "year": "Año"})
        st.plotly_chart(fig_year, use_container_width=True)
        st.caption("👉 Evolución histórica de la cantidad de procesos por año.")
        
        if year_stats["monto_total"].sum() > 0:
            fig_year_monto = px.line(year_stats, x="year", y="monto_total",
                                      title="💰 Evolución Anual de Montos Totales (2015-2025)",
                                      markers=True,
                                      labels={"monto_total": "Monto Total ($)", "year": "Año"})
            st.plotly_chart(fig_year_monto, use_container_width=True)
            st.caption("👉 Evolución histórica de los montos contratados por año.")

    if "tipo_contratacion" in df.columns and df["monto_total"].sum() > 0:
        tipo_monto = df.groupby("tipo_contratacion")["monto_total"].sum().reset_index()
        tipo_monto = tipo_monto[tipo_monto["monto_total"] > 0]
        if not tipo_monto.empty:
            fig1 = px.bar(tipo_monto, x="tipo_contratacion", y="monto_total",
                          title="a) Monto Total por Tipo de Contratación",
                          color="tipo_contratacion", text_auto=".2s",
                          labels={"monto_total": "Monto Total ($)", "tipo_contratacion": "Tipo de Contratación"})
            st.plotly_chart(fig1, use_container_width=True)
            st.caption("👉 Se observa el monto total por tipo de contratación en el período analizado.")

    if "tipo_contratacion" in df.columns:
        tipo_count = df["tipo_contratacion"].value_counts().reset_index()
        tipo_count.columns = ["tipo_contratacion", "cantidad"]
        fig2 = px.bar(tipo_count, x="tipo_contratacion", y="cantidad",
                      title="b) Cantidad de Procesos por Tipo de Contratación",
                      color="tipo_contratacion", text_auto=True,
                      labels={"cantidad": "Cantidad de Procesos", "tipo_contratacion": "Tipo de Contratación"})
        st.plotly_chart(fig2, use_container_width=True)
        st.caption("👉 Se observa la frecuencia de cada tipo de contratación.")

    if "month" in df.columns and not analizar_todos_anos:
        mes_count = df.groupby("month").size().reset_index(name="cantidad")
        fig2 = px.line(mes_count, x="month", y="cantidad",
                       title="b) Evolución Mensual de Procesos de Contratación",
                       markers=True,
                       labels={"cantidad": "Cantidad de Procesos", "month": "Mes"})
        st.plotly_chart(fig2, use_container_width=True)
        st.caption("👉 Se aprecian los meses con mayor actividad en contratación pública.")

    if "month" in df.columns and df["monto_total"].sum() > 0 and not analizar_todos_anos:
        mes_monto = df.groupby("month")["monto_total"].sum().reset_index()
        fig3 = px.line(mes_monto, x="month", y="monto_total",
                       title="c) Evolución Mensual de Montos Totales",
                       markers=True,
                       labels={"monto_total": "Monto Total ($)", "month": "Mes"})
        st.plotly_chart(fig3, use_container_width=True)
        st.caption("👉 Se aprecian los meses con mayores montos contratados.")

    if "entidad_compradora" in df.columns:
        top_buyers = df["entidad_compradora"].value_counts().head(10).reset_index()
        top_buyers.columns = ["entidad_compradora", "cantidad"]
        fig4 = px.bar(top_buyers, x="cantidad", y="entidad_compradora",
                      title="d) Top 10 Entidades Compradoras",
                      orientation="h",
                      labels={"cantidad": "Cantidad de Procesos", "entidad_compradora": "Entidad"})
        st.plotly_chart(fig4, use_container_width=True)
        st.caption("👉 Entidades con mayor cantidad de procesos de contratación.")

    if "tipo_contratacion" in df.columns:
        fig4 = px.pie(df, names="tipo_contratacion",
                      title="d) Proporción de Contratos por Tipo")
        st.plotly_chart(fig4, use_container_width=True)
        st.caption("👉 Representación porcentual de la distribución de procesos por tipo.")

    if "month" in df.columns and "tipo_contratacion" in df.columns and not analizar_todos_anos:
        tipo_mes = df.groupby(["month", "tipo_contratacion"]).size().reset_index(name="cantidad")
        fig5 = px.bar(tipo_mes, x="month", y="cantidad", 
                      color="tipo_contratacion",
                      title="e) Procesos por Mes y Tipo de Contratación",
                      barmode="stack",
                      labels={"cantidad": "Cantidad de Procesos", "month": "Mes", "tipo_contratacion": "Tipo"})
        st.plotly_chart(fig5, use_container_width=True)
        st.caption("👉 Distribución mensual detallada por tipo de contratación.")

    if "proveedor" in df.columns:
        top_suppliers = df["proveedor"].value_counts().head(10).reset_index()
        top_suppliers.columns = ["proveedor", "cantidad"]
        fig6 = px.bar(top_suppliers, x="cantidad", y="proveedor",
                      title="f) Top 10 Proveedores",
                      orientation="h",
                      labels={"cantidad": "Contratos Ganados", "proveedor": "Proveedor"})
        st.plotly_chart(fig6, use_container_width=True)
        st.caption("👉 Proveedores con mayor cantidad de contratos adjudicados.")

    # Gráfica comparativa de tipos de contratación por año
    if "year" in df.columns and "tipo_contratacion" in df.columns:
        tipo_year = df.groupby(["year", "tipo_contratacion"]).size().reset_index(name="cantidad")
        
        fig_comp = px.line(tipo_year, x="year", y="cantidad", 
                          color="tipo_contratacion",
                          title="g) Comparativa de Tipos de Contratación por Año",
                          markers=True,
                          labels={"cantidad": "Cantidad de Procesos", "year": "Año", "tipo_contratacion": "Tipo"})
        st.plotly_chart(fig_comp, use_container_width=True)
        st.caption("👉 Evolución temporal de cada tipo de contratación a lo largo de los años analizados.")
        
        # Versión alternativa con montos (si están disponibles)
        if df["monto_total"].sum() > 0:
            tipo_year_monto = df.groupby(["year", "tipo_contratacion"])["monto_total"].sum().reset_index()
            tipo_year_monto = tipo_year_monto[tipo_year_monto["monto_total"] > 0]
            
            if not tipo_year_monto.empty:
                fig_comp_monto = px.line(tipo_year_monto, x="year", y="monto_total", 
                                        color="tipo_contratacion",
                                        title="h) Comparativa de Montos por Tipo de Contratación y Año",
                                        markers=True,
                                        labels={"monto_total": "Monto Total ($)", "year": "Año", "tipo_contratacion": "Tipo"})
                st.plotly_chart(fig_comp_monto, use_container_width=True)
                st.caption("👉 Evolución de los montos contratados por tipo a lo largo de los años.")

    st.subheader("💾 Exportar resultados")

    csv = df.to_csv(index=False).encode("utf-8")
    
    if analizar_todos_anos:
        filename = f"compras_publicas_2015-2025"
    else:
        filename = f"compras_publicas_{years[0]}"
    
    if tipo_contratacion != "TODAS":
        filename += f"_{tipo_contratacion.replace(' ', '_')}"
    if region != "TODAS":
        filename += f"_{region.replace(' ', '_')}"
    filename += ".csv"
    
    st.download_button(
        "📥 Descargar datos limpios (CSV)",
        csv,
        filename,
        "text/csv",
        key="download-csv"
    )
   
    st.subheader("🧠 Conclusiones del análisis")
    
    periodo_texto = "2015-2025" if analizar_todos_anos else str(years[0])
    
    st.markdown(f"""
    ### Hallazgos Principales:
    
    - **Volumen de Datos:** Se identificaron {total_registros:,} procesos de contratación en el período {periodo_texto}.
      {f"Filtrando por tipo: **{tipo_contratacion}**" if tipo_contratacion != "TODAS" else "Incluye todos los tipos de contratación."}
      {f" en la provincia de **{region}**" if region != "TODAS" else ""}
      
    - **Distribución por Tipo:** Los tipos de contratación más frecuentes reflejan las prioridades de inversión pública 
      en el sector analizado.
      
    - **Patrones Temporales:** Se identifican picos de contratación en ciertos períodos, posiblemente vinculados a:
      - Ciclos presupuestarios gubernamentales
      - Ejecución de proyectos anuales
      - Procesos de cierre fiscal
      {f"- Tendencias históricas de {len(years)} años analizados" if analizar_todos_anos else ""}
      
    - **Actores Principales:** 
      - {entidades_unicas} entidades compradoras participaron en el proceso
      - {proveedores_unicos} proveedores únicos fueron adjudicados
      
    ### Aplicaciones Prácticas:
    
    Este análisis puede servir para:
    - Monitoreo de transparencia en contratación pública
    - Identificación de patrones de adjudicación
    - Análisis de competitividad entre proveedores
    - Optimización de procesos de contratación
    - Desarrollo de políticas públicas basadas en evidencia
    {f"- Análisis de tendencias históricas y evolutivas (2015-2025)" if analizar_todos_anos else ""}
    
    """)

else:
    st.info("""
    ### Instrucciones de uso:
    
    1. **[NUEVO] Marca el checkbox** si deseas analizar todos los años (2015-2025)
    2. **O selecciona un año específico** para análisis individual
    3. **Elige la provincia** (o "TODAS" para todo el país)
    4. **Elige el tipo de contratación** (o selecciona "TODAS" para todos los tipos)
    5. **Haz clic en "🔍 Cargar datos"** para comenzar el análisis
    
    ⚠️ **Importante:** 
    - El análisis multi-año (2015-2025) descargará datos de 11 años y puede tardar bastante tiempo
    - El sistema descargará TODOS los datos disponibles según los filtros seleccionados
    - Esto puede tardar varios minutos dependiendo de la cantidad de registros
    
    **Tipos de contratación disponibles:**
    - Bienes, Obras, Servicios, Consultoría
    - Licitación, Menor Cuantía, Ínfima Cuantía
    - Subasta, Catálogo
    
    El sistema generará automáticamente:
    - Estadísticas descriptivas completas
    - Visualizaciones interactivas (incluye análisis temporal multi-año)
    - Análisis de entidades y proveedores
    - Datos exportables en CSV
    
    **Nota:** Este análisis usa el endpoint oficial `/search_ocds` de la API de Compras Públicas de Ecuador.
    """)