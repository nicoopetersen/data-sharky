"""Grafica originaciones vs defaults mensuales de Sharky (Fase 1) -> HTML interactivo."""
import pandas as pd
import plotly.graph_objects as go

df = pd.read_csv("data/sharky_fase1_conteos.csv")
piv = (df[df.metric.isin(["ORIGINACIONES_POR_MES", "DEFAULTS_POR_MES"])]
       .pivot(index="mes", columns="metric", values="n").sort_index())

fig = go.Figure()
fig.add_bar(x=piv.index, y=piv["ORIGINACIONES_POR_MES"], name="Originaciones",
            marker_color="#2563eb")
fig.add_bar(x=piv.index, y=piv["DEFAULTS_POR_MES"], name="Defaults (foreclosures)",
            marker_color="#dc2626")
# tasa de default mensual aproximada (defaults del mes / originaciones del mes)
rate = (piv["DEFAULTS_POR_MES"] / piv["ORIGINACIONES_POR_MES"] * 100).round(1)
fig.add_scatter(x=piv.index, y=rate, name="Defaults/Originaciones del mes (%)",
                yaxis="y2", mode="lines+markers", line=dict(color="#f59e0b", width=3))

fig.update_layout(
    title="Sharky.fi — Originaciones vs Defaults por mes (últimos 6 meses)<br>"
          "<sub>Fuente: Dune sharky_solana · datos hasta 2026-07-10 (ene y jul parciales)</sub>",
    barmode="group", template="plotly_white",
    yaxis=dict(title="Cantidad de préstamos"),
    yaxis2=dict(title="%", overlaying="y", side="right", showgrid=False, range=[0, max(rate)*1.4]),
    legend=dict(orientation="h", y=-0.2), height=520,
)
out = "reports/sharky_fase1_originaciones_vs_defaults.html"
fig.write_html(out)
print("guardado:", out)
