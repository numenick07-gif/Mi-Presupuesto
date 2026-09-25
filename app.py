"""Interfaz web de MiPresupuesto — gestión y análisis de finanzas personales."""

from __future__ import annotations

from datetime import date
from io import BytesIO

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from modules.analisis import (
    calcular_balance,
    calcular_gastos,
    calcular_ingresos,
    calcular_porcentaje_gastos,
    categoria_mayor_gasto,
    contar_movimientos,
    evolucion_mensual,
    filtrar_movimientos,
    formatear_moneda,
    formatear_porcentaje,
    gastos_por_categoria,
    ingresos_por_categoria,
    ordenar_movimientos,
    promedio_mensual,
)
from modules.data_manager import (
    actualizar_movimiento,
    cargar_movimientos,
    cargar_presupuestos,
    eliminar_movimiento,
    guardar_limite_presupuesto,
)
from modules.gastos import CATEGORIAS_GASTO, METODOS_PAGO, registrar_gasto
from modules.ingresos import CATEGORIAS_INGRESO, FUENTES_INGRESO, registrar_ingreso
from modules.presupuesto import (
    ESTADO_CERCA,
    ESTADO_DENTRO,
    ESTADO_EXCEDIDO,
    calcular_presupuesto,
)

NOMBRES_MESES = {
    1: "Enero",
    2: "Febrero",
    3: "Marzo",
    4: "Abril",
    5: "Mayo",
    6: "Junio",
    7: "Julio",
    8: "Agosto",
    9: "Septiembre",
    10: "Octubre",
    11: "Noviembre",
    12: "Diciembre",
}

COLOR_INGRESO = "#1f6f4a"
COLOR_GASTO = "#b45309"
COLOR_BALANCE = "#1d4ed8"
COLORES_GRAFICOS = [
    "#1f6f4a",
    "#1d4ed8",
    "#b45309",
    "#0f766e",
    "#6b21a8",
    "#9f1239",
    "#334155",
    "#0369a1",
    "#854d0e",
]


def configurar_pagina() -> None:
    st.set_page_config(
        page_title="MiPresupuesto",
        page_icon="💰",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(
        """
        <style>
            .block-container {padding-top: 1.5rem; padding-bottom: 2rem;}
            div[data-testid="stMetric"] {
                background-color: #f8fafc;
                border: 1px solid #e2e8f0;
                padding: 0.75rem 1rem;
                border-radius: 0.6rem;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def tabla_para_mostrar(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    vista = df.copy()
    if "fecha" in vista.columns:
        vista["fecha"] = pd.to_datetime(vista["fecha"], errors="coerce").dt.strftime("%Y-%m-%d")
    if "monto" in vista.columns:
        vista["monto"] = pd.to_numeric(vista["monto"], errors="coerce").fillna(0)
        vista["monto_formateado"] = vista["monto"].map(formatear_moneda)
    columnas = [
        col
        for col in [
            "id",
            "fecha",
            "tipo",
            "descripcion",
            "categoria",
            "monto_formateado",
            "fuente",
            "metodo_pago",
        ]
        if col in vista.columns
    ]
    nombres = {
        "id": "ID",
        "fecha": "Fecha",
        "tipo": "Tipo",
        "descripcion": "Descripción",
        "categoria": "Categoría",
        "monto_formateado": "Monto",
        "fuente": "Fuente",
        "metodo_pago": "Método de pago",
    }
    return vista[columnas].rename(columns=nombres)


def recargar_datos() -> pd.DataFrame:
    return cargar_movimientos()


def pagina_dashboard(df: pd.DataFrame) -> None:
    st.title("Dashboard")
    st.caption("Resumen de ingresos, gastos e indicadores en pesos dominicanos (RD$).")

    col_f1, col_f2, col_f3 = st.columns(3)
    fechas = pd.to_datetime(df["fecha"], errors="coerce") if not df.empty else pd.Series(dtype="datetime64[ns]")
    anios = sorted(fechas.dt.year.dropna().unique().tolist()) if not fechas.empty else [date.today().year]
    with col_f1:
        anio = st.selectbox("Año", ["Todos"] + [int(a) for a in anios], key="dash_anio")
    with col_f2:
        mes = st.selectbox(
            "Mes",
            ["Todos"] + [NOMBRES_MESES[m] for m in range(1, 13)],
            key="dash_mes",
        )
    with col_f3:
        tipo = st.selectbox("Tipo", ["Todos", "ingreso", "gasto"], key="dash_tipo")

    anio_filtro = None if anio == "Todos" else int(anio)
    mes_filtro = None if mes == "Todos" else [k for k, v in NOMBRES_MESES.items() if v == mes][0]
    filtrado = filtrar_movimientos(df, tipo=None if tipo == "Todos" else tipo, anio=anio_filtro, mes=mes_filtro)

    ingresos = calcular_ingresos(filtrado)
    gastos = calcular_gastos(filtrado)
    balance = calcular_balance(filtrado)
    porcentaje = calcular_porcentaje_gastos(filtrado)
    total_mov = contar_movimientos(filtrado)

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Ingresos", formatear_moneda(ingresos))
    m2.metric("Gastos", formatear_moneda(gastos))
    m3.metric("Balance", formatear_moneda(balance))
    m4.metric("% utilizado", formatear_porcentaje(porcentaje))
    m5.metric("Movimientos", f"{total_mov}")

    if filtrado.empty:
        st.info("No hay movimientos para los filtros seleccionados.")
        return

    g1, g2 = st.columns(2)
    with g1:
        st.subheader("Ingresos vs. gastos")
        fig_vs = go.Figure(
            data=[
                go.Bar(name="Ingresos", x=["Totales"], y=[ingresos], marker_color=COLOR_INGRESO),
                go.Bar(name="Gastos", x=["Totales"], y=[gastos], marker_color=COLOR_GASTO),
            ]
        )
        fig_vs.update_layout(barmode="group", yaxis_title="Monto (RD$)", height=360, margin=dict(t=30))
        st.plotly_chart(fig_vs, use_container_width=True)

    with g2:
        st.subheader("Gastos por categoría")
        gastos_cat = gastos_por_categoria(filtrado)
        if gastos_cat.empty:
            st.info("No hay gastos para graficar.")
        else:
            fig_cat = px.bar(
                gastos_cat,
                x="categoria",
                y="total",
                color="categoria",
                color_discrete_sequence=COLORES_GRAFICOS,
            )
            fig_cat.update_layout(
                showlegend=False,
                xaxis_title="Categoría",
                yaxis_title="Monto (RD$)",
                height=360,
                margin=dict(t=30),
            )
            st.plotly_chart(fig_cat, use_container_width=True)

    g3, g4 = st.columns(2)
    with g3:
        st.subheader("Evolución mensual")
        mensual = evolucion_mensual(filtrado)
        if mensual.empty:
            st.info("No hay datos mensuales suficientes.")
        else:
            fig_lin = go.Figure()
            fig_lin.add_trace(
                go.Scatter(
                    x=mensual["periodo"],
                    y=mensual["ingresos"],
                    name="Ingresos",
                    mode="lines+markers",
                    line=dict(color=COLOR_INGRESO),
                )
            )
            fig_lin.add_trace(
                go.Scatter(
                    x=mensual["periodo"],
                    y=mensual["gastos"],
                    name="Gastos",
                    mode="lines+markers",
                    line=dict(color=COLOR_GASTO),
                )
            )
            fig_lin.update_layout(xaxis_title="Período", yaxis_title="Monto (RD$)", height=360, margin=dict(t=30))
            st.plotly_chart(fig_lin, use_container_width=True)

    with g4:
        st.subheader("Distribución porcentual de gastos")
        gastos_cat = gastos_por_categoria(filtrado)
        if gastos_cat.empty:
            st.info("No hay gastos para mostrar la distribución.")
        else:
            fig_pie = px.pie(
                gastos_cat,
                names="categoria",
                values="total",
                color_discrete_sequence=COLORES_GRAFICOS,
            )
            fig_pie.update_layout(height=360, margin=dict(t=30))
            st.plotly_chart(fig_pie, use_container_width=True)


def pagina_ingresos() -> None:
    st.title("Registrar ingreso")
    st.caption("Capture un ingreso en pesos dominicanos. Todos los campos son obligatorios.")

    with st.form("form_ingreso", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            fecha = st.date_input("Fecha", value=date.today())
            categoria = st.selectbox("Categoría", CATEGORIAS_INGRESO)
            fuente = st.selectbox("Fuente", FUENTES_INGRESO)
        with c2:
            descripcion = st.text_input("Descripción")
            monto = st.number_input("Monto (RD$)", min_value=0.0, step=100.0, format="%.2f")
        enviar = st.form_submit_button("Guardar ingreso")

    if enviar:
        ok, mensaje, _ = registrar_ingreso(fecha, descripcion, categoria, monto, fuente)
        if ok:
            st.success(mensaje)
        else:
            st.error(mensaje)


def pagina_gastos() -> None:
    st.title("Registrar gasto")
    st.caption("Capture un gasto en pesos dominicanos. Todos los campos son obligatorios.")

    with st.form("form_gasto", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            fecha = st.date_input("Fecha", value=date.today())
            categoria = st.selectbox("Categoría", CATEGORIAS_GASTO)
            metodo = st.selectbox("Método de pago", METODOS_PAGO)
        with c2:
            descripcion = st.text_input("Descripción")
            monto = st.number_input("Monto (RD$)", min_value=0.0, step=100.0, format="%.2f")
        enviar = st.form_submit_button("Guardar gasto")

    if enviar:
        ok, mensaje, _ = registrar_gasto(fecha, descripcion, categoria, monto, metodo)
        if ok:
            st.success(mensaje)
        else:
            st.error(mensaje)


def _bytes_excel(df: pd.DataFrame) -> bytes:
    buffer = BytesIO()
    exportable = df.copy()
    if "fecha" in exportable.columns:
        exportable["fecha"] = pd.to_datetime(exportable["fecha"], errors="coerce").dt.strftime("%Y-%m-%d")
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        exportable.to_excel(writer, index=False, sheet_name="movimientos")
    return buffer.getvalue()


def pagina_movimientos(df: pd.DataFrame) -> None:
    st.title("Historial de movimientos")
    st.caption("Consulte, filtre, edite o elimine ingresos y gastos registrados.")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        tipo = st.selectbox("Tipo", ["Todos", "ingreso", "gasto"], key="hist_tipo")
    with c2:
        categorias = ["Todas"] + sorted(df["categoria"].dropna().unique().tolist()) if not df.empty else ["Todas"]
        categoria = st.selectbox("Categoría", categorias, key="hist_cat")
    with c3:
        orden_campo = st.selectbox("Ordenar por", ["fecha", "monto"], key="hist_orden")
    with c4:
        orden_dir = st.selectbox("Dirección", ["Descendente", "Ascendente"], key="hist_dir")

    d1, d2, d3 = st.columns(3)
    min_fecha = pd.to_datetime(df["fecha"]).min().date() if not df.empty else date.today()
    max_fecha = pd.to_datetime(df["fecha"]).max().date() if not df.empty else date.today()
    with d1:
        fecha_inicio = st.date_input("Desde", value=min_fecha, key="hist_desde")
    with d2:
        fecha_fin = st.date_input("Hasta", value=max_fecha, key="hist_hasta")
    with d3:
        busqueda = st.text_input("Buscar descripción", key="hist_busqueda")

    filtrado = filtrar_movimientos(
        df,
        tipo=None if tipo == "Todos" else tipo,
        categoria=None if categoria == "Todas" else categoria,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        busqueda=busqueda,
    )
    filtrado = ordenar_movimientos(filtrado, campo=orden_campo, ascendente=orden_dir == "Ascendente")

    st.dataframe(tabla_para_mostrar(filtrado), use_container_width=True, hide_index=True)
    st.caption(f"{len(filtrado)} movimiento(s) según los filtros actuales.")

    e1, e2 = st.columns(2)
    csv_bytes = filtrado.to_csv(index=False).encode("utf-8-sig")
    with e1:
        st.download_button(
            "Descargar CSV",
            data=csv_bytes,
            file_name="movimientos.csv",
            mime="text/csv",
            disabled=filtrado.empty,
        )
    with e2:
        st.download_button(
            "Descargar Excel",
            data=_bytes_excel(filtrado) if not filtrado.empty else b"",
            file_name="movimientos.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            disabled=filtrado.empty,
        )

    st.divider()
    st.subheader("Editar movimiento")
    if filtrado.empty:
        st.info("No hay movimientos para editar.")
    else:
        ids = filtrado["id"].tolist()
        id_editar = st.selectbox("Seleccione el ID", ids, key="edit_id")
        registro = filtrado.loc[filtrado["id"] == id_editar].iloc[0]
        tipo_actual = str(registro["tipo"])
        categorias_edit = CATEGORIAS_INGRESO if tipo_actual == "ingreso" else CATEGORIAS_GASTO
        categoria_actual = str(registro["categoria"])
        indice_cat = categorias_edit.index(categoria_actual) if categoria_actual in categorias_edit else 0

        with st.form("form_editar"):
            c1, c2 = st.columns(2)
            with c1:
                fecha_e = st.date_input("Fecha", value=pd.to_datetime(registro["fecha"]).date())
                categoria_e = st.selectbox("Categoría", categorias_edit, index=indice_cat)
                if tipo_actual == "ingreso":
                    fuentes = FUENTES_INGRESO
                    fuente_actual = str(registro["fuente"])
                    idx_fuente = fuentes.index(fuente_actual) if fuente_actual in fuentes else 0
                    extra = st.selectbox("Fuente", fuentes, index=idx_fuente)
                else:
                    metodos = METODOS_PAGO
                    metodo_actual = str(registro["metodo_pago"])
                    idx_metodo = metodos.index(metodo_actual) if metodo_actual in metodos else 0
                    extra = st.selectbox("Método de pago", metodos, index=idx_metodo)
            with c2:
                descripcion_e = st.text_input("Descripción", value=str(registro["descripcion"]))
                monto_e = st.number_input(
                    "Monto (RD$)",
                    min_value=0.0,
                    step=100.0,
                    format="%.2f",
                    value=float(registro["monto"]),
                )
            guardar = st.form_submit_button("Guardar cambios")

        if guardar:
            datos = {
                "fecha": fecha_e,
                "tipo": tipo_actual,
                "descripcion": descripcion_e,
                "categoria": categoria_e,
                "monto": monto_e,
                "fuente": extra if tipo_actual == "ingreso" else "",
                "metodo_pago": extra if tipo_actual == "gasto" else "",
            }
            ok, mensaje, _ = actualizar_movimiento(int(id_editar), datos)
            if ok:
                st.success(mensaje)
                st.rerun()
            else:
                st.error(mensaje)

    st.divider()
    st.subheader("Eliminar movimiento")
    if df.empty:
        st.info("No hay movimientos para eliminar.")
    else:
        id_borrar = st.selectbox("ID a eliminar", df["id"].tolist(), key="del_id")
        if st.button("Eliminar", type="primary"):
            ok, mensaje, _ = eliminar_movimiento(int(id_borrar))
            if ok:
                st.success(mensaje)
                st.rerun()
            else:
                st.error(mensaje)


def pagina_presupuesto(df: pd.DataFrame) -> None:
    st.title("Presupuesto por categoría")
    st.caption("Establezca un límite mensual y compare el gasto actual del período seleccionado.")

    presupuestos = cargar_presupuestos()
    fechas = pd.to_datetime(df["fecha"], errors="coerce") if not df.empty else pd.Series(dtype="datetime64[ns]")
    anios = sorted(fechas.dt.year.dropna().unique().tolist()) if not fechas.empty else [date.today().year]
    hoy = date.today()

    c1, c2 = st.columns(2)
    with c1:
        anio = st.selectbox("Año", [int(a) for a in anios] or [hoy.year], index=len(anios) - 1 if anios else 0)
    with c2:
        mes_default = hoy.month if hoy.year in anios else 1
        mes = st.selectbox(
            "Mes",
            list(range(1, 13)),
            format_func=lambda m: NOMBRES_MESES[m],
            index=mes_default - 1,
        )

    st.subheader("Definir límite mensual")
    with st.form("form_presupuesto"):
        p1, p2 = st.columns(2)
        with p1:
            categoria = st.selectbox("Categoría de gasto", CATEGORIAS_GASTO)
        with p2:
            limite = st.number_input("Límite mensual (RD$)", min_value=0.0, step=500.0, format="%.2f")
        guardar = st.form_submit_button("Guardar presupuesto")

    if guardar:
        ok, mensaje, presupuestos = guardar_limite_presupuesto(categoria, limite)
        if ok:
            st.success(mensaje)
        else:
            st.error(mensaje)

    comparacion = calcular_presupuesto(df, presupuestos, anio=int(anio), mes=int(mes))
    if comparacion.empty:
        st.info("Aún no hay presupuestos registrados.")
        return

    st.subheader(f"Estado de {NOMBRES_MESES[int(mes)]} {anio}")
    for _, fila in comparacion.iterrows():
        porcentaje = min(float(fila["porcentaje_utilizado"]), 100.0)
        estado = str(fila["estado"])

        st.markdown(f"**{fila['categoria']}** — {estado}")
        col_a, col_b, col_c, col_d = st.columns(4)
        col_a.write(f"Presupuesto: {formatear_moneda(fila['presupuesto'])}")
        col_b.write(f"Gasto actual: {formatear_moneda(fila['gasto_actual'])}")
        col_c.write(f"Restante: {formatear_moneda(fila['restante'])}")
        col_d.write(f"Utilizado: {formatear_porcentaje(fila['porcentaje_utilizado'])}")
        st.progress(porcentaje / 100.0)
        if estado == ESTADO_EXCEDIDO:
            st.error("El gasto superó el límite mensual de esta categoría.")
        elif estado == ESTADO_CERCA:
            st.warning("El gasto se encuentra cerca del límite.")
        else:
            st.caption("El gasto se mantiene dentro del presupuesto.")
        st.divider()

    vista = comparacion.copy()
    vista["presupuesto"] = vista["presupuesto"].map(formatear_moneda)
    vista["gasto_actual"] = vista["gasto_actual"].map(formatear_moneda)
    vista["restante"] = vista["restante"].map(formatear_moneda)
    vista["porcentaje_utilizado"] = vista["porcentaje_utilizado"].map(formatear_porcentaje)
    vista = vista.rename(
        columns={
            "categoria": "Categoría",
            "presupuesto": "Presupuesto",
            "gasto_actual": "Gasto actual",
            "restante": "Restante",
            "porcentaje_utilizado": "% utilizado",
            "estado": "Estado",
        }
    )
    st.dataframe(vista, use_container_width=True, hide_index=True)


def pagina_analisis(df: pd.DataFrame) -> None:
    st.title("Análisis financiero")
    st.caption("Los indicadores se calculan únicamente con los movimientos registrados. No se emiten recomendaciones.")

    fechas = pd.to_datetime(df["fecha"], errors="coerce") if not df.empty else pd.Series(dtype="datetime64[ns]")
    anios = ["Todos"] + [int(a) for a in sorted(fechas.dt.year.dropna().unique().tolist())] if not fechas.empty else ["Todos"]
    categorias = ["Todas"] + sorted(df["categoria"].dropna().unique().tolist()) if not df.empty else ["Todas"]

    f1, f2, f3, f4 = st.columns(4)
    with f1:
        anio = st.selectbox("Año", anios, key="an_anio")
    with f2:
        mes = st.selectbox("Mes", ["Todos"] + [NOMBRES_MESES[m] for m in range(1, 13)], key="an_mes")
    with f3:
        categoria = st.selectbox("Categoría", categorias, key="an_cat")
    with f4:
        tipo = st.selectbox("Tipo", ["Todos", "ingreso", "gasto"], key="an_tipo")

    anio_filtro = None if anio == "Todos" else int(anio)
    mes_filtro = None if mes == "Todos" else [k for k, v in NOMBRES_MESES.items() if v == mes][0]
    filtrado = filtrar_movimientos(
        df,
        tipo=None if tipo == "Todos" else tipo,
        categoria=None if categoria == "Todas" else categoria,
        anio=anio_filtro,
        mes=mes_filtro,
    )

    ingresos = calcular_ingresos(filtrado)
    gastos = calcular_gastos(filtrado)
    balance = calcular_balance(filtrado)
    porcentaje = calcular_porcentaje_gastos(filtrado)
    mayor_cat, mayor_monto = categoria_mayor_gasto(filtrado)
    prom_gastos = promedio_mensual(filtrado, "gasto")
    prom_ingresos = promedio_mensual(filtrado, "ingreso")

    k1, k2, k3 = st.columns(3)
    k1.metric("Promedio mensual de ingresos", formatear_moneda(prom_ingresos))
    k2.metric("Promedio mensual de gastos", formatear_moneda(prom_gastos))
    k3.metric("% de ingresos destinado a gastos", formatear_porcentaje(porcentaje))

    k4, k5, k6 = st.columns(3)
    k4.metric("Balance del período", formatear_moneda(balance))
    k5.metric("Categoría con mayor gasto", mayor_cat)
    k6.metric("Monto de esa categoría", formatear_moneda(mayor_monto))

    t1, t2 = st.columns(2)
    with t1:
        st.subheader("Ingresos por categoría")
        tabla_ing = ingresos_por_categoria(filtrado)
        if tabla_ing.empty:
            st.info("No hay ingresos en el período.")
        else:
            mostrar = tabla_ing.copy()
            mostrar["total"] = mostrar["total"].map(formatear_moneda)
            st.dataframe(
                mostrar.rename(columns={"categoria": "Categoría", "total": "Total"}),
                use_container_width=True,
                hide_index=True,
            )
    with t2:
        st.subheader("Gastos por categoría")
        tabla_gas = gastos_por_categoria(filtrado)
        if tabla_gas.empty:
            st.info("No hay gastos en el período.")
        else:
            mostrar = tabla_gas.copy()
            mostrar["total"] = mostrar["total"].map(formatear_moneda)
            st.dataframe(
                mostrar.rename(columns={"categoria": "Categoría", "total": "Total"}),
                use_container_width=True,
                hide_index=True,
            )

    st.subheader("Balance mensual")
    mensual = evolucion_mensual(filtrado)
    if mensual.empty:
        st.info("No hay datos suficientes para el análisis mensual.")
    else:
        vista = mensual.copy()
        for col in ["ingresos", "gastos", "balance"]:
            vista[col] = vista[col].map(formatear_moneda)
        st.dataframe(
            vista.rename(
                columns={
                    "periodo": "Período",
                    "ingresos": "Ingresos",
                    "gastos": "Gastos",
                    "balance": "Balance",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

        fig = go.Figure()
        fig.add_trace(
            go.Bar(name="Ingresos", x=mensual["periodo"], y=mensual["ingresos"], marker_color=COLOR_INGRESO)
        )
        fig.add_trace(
            go.Bar(name="Gastos", x=mensual["periodo"], y=mensual["gastos"], marker_color=COLOR_GASTO)
        )
        fig.add_trace(
            go.Scatter(
                name="Balance",
                x=mensual["periodo"],
                y=mensual["balance"],
                mode="lines+markers",
                line=dict(color=COLOR_BALANCE),
            )
        )
        fig.update_layout(barmode="group", yaxis_title="Monto (RD$)", height=420)
        st.plotly_chart(fig, use_container_width=True)

        e1, e2 = st.columns(2)
        with e1:
            st.subheader("Evolución de ingresos")
            fig_i = px.line(mensual, x="periodo", y="ingresos", markers=True)
            fig_i.update_traces(line_color=COLOR_INGRESO)
            fig_i.update_layout(xaxis_title="Período", yaxis_title="Monto (RD$)", height=320)
            st.plotly_chart(fig_i, use_container_width=True)
        with e2:
            st.subheader("Evolución de gastos")
            fig_g = px.line(mensual, x="periodo", y="gastos", markers=True)
            fig_g.update_traces(line_color=COLOR_GASTO)
            fig_g.update_layout(xaxis_title="Período", yaxis_title="Monto (RD$)", height=320)
            st.plotly_chart(fig_g, use_container_width=True)

    st.download_button(
        "Descargar análisis filtrado (CSV)",
        data=filtrado.to_csv(index=False).encode("utf-8-sig"),
        file_name="analisis_movimientos.csv",
        mime="text/csv",
        disabled=filtrado.empty,
    )


def pagina_acerca() -> None:
    st.title("Acerca de MiPresupuesto")
    st.write(
        "MiPresupuesto es un sistema académico de gestión y análisis de finanzas personales. "
        "Permite registrar ingresos y gastos, consultar movimientos, definir presupuestos por "
        "categoría y visualizar indicadores en pesos dominicanos (RD$)."
    )
    st.write(
        "Los datos son ficticios o introducidos por el usuario. La aplicación no se conecta a "
        "bancos, no almacena información sensible de tarjetas y no ofrece recomendaciones financieras."
    )
    st.markdown("**Tecnologías:** Python, Streamlit, Pandas, Plotly y persistencia en CSV.")
    st.markdown("**Autor:** *[Nombre del estudiante]*")


def main() -> None:
    configurar_pagina()
    with st.sidebar:
        st.title("MiPresupuesto")
        st.caption("Finanzas personales en RD$")
        seccion = st.radio(
            "Navegación",
            [
                "🏠 Dashboard",
                "💰 Ingresos",
                "💸 Gastos",
                "📋 Movimientos",
                "🎯 Presupuesto",
                "📊 Análisis",
                "ℹ️ Acerca de",
            ],
        )
        st.divider()
        st.caption("Laboratorio de programación en Python")

    df = recargar_datos()

    if seccion.endswith("Dashboard"):
        pagina_dashboard(df)
    elif seccion.endswith("Ingresos"):
        pagina_ingresos()
    elif seccion.endswith("Gastos"):
        pagina_gastos()
    elif seccion.endswith("Movimientos"):
        pagina_movimientos(df)
    elif seccion.endswith("Presupuesto"):
        pagina_presupuesto(df)
    elif seccion.endswith("Análisis"):
        pagina_analisis(df)
    else:
        pagina_acerca()


if __name__ == "__main__":
    main()
