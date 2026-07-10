"""Fase 2 — clasificación underwater de defaults de Sharky + chart. Robusto a supuestos."""
import pandas as pd
import plotly.graph_objects as go

df = pd.read_parquet("data/sharky_fase2b_floor.parquet")
tot_matched = len(df)
d = df[df["floor_p15_sol"].notna() & df["principal_sol"].notna()].copy()
n = len(d)

def uw(debt_mult, floor_col):
    debt = d["principal_sol"] * debt_mult
    return (debt > d[floor_col]).mean() * 100

print(f"Defaults con floor estimable: {n} (de {tot_matched} matcheados)\n")
print("=== % UNDERWATER según supuestos (floor y multiplicador de interés) ===")
grid = []
for fcol, fname in [("floor_p15_sol", "floor p15 (bajo)"), ("floor_median_sol", "floor mediana")]:
    for m, mn in [(1.00, "principal"), (1.05, "+5% int"), (1.10, "+10% int")]:
        pct = uw(m, fcol)
        grid.append((fname, mn, pct))
        print(f"  {fname:18} · deuda={mn:10} -> {pct:5.1f}% underwater")

# Caso base para reportar: floor p15, deuda = principal * 1.05
d["debt_sol"] = d["principal_sol"] * 1.05
d["underwater"] = d["debt_sol"] > d["floor_p15_sol"]
base_uw = d["underwater"].mean() * 100
n_uw = int(d["underwater"].sum())
print(f"\n=== CASO BASE (floor p15 · deuda = principal x1.05) ===")
print(f"Underwater: {n_uw} / {n} = {base_uw:.1f}%")
print(f"No-underwater (default con NFT aún > deuda): {n - n_uw} = {100-base_uw:.1f}%")

# value-weighted (por SOL de principal)
sol_uw = d.loc[d.underwater, "principal_sol"].sum()
sol_all = d["principal_sol"].sum()
print(f"\nPonderado por SOL de principal: {sol_uw:.0f} / {sol_all:.0f} SOL = {100*sol_uw/sol_all:.1f}% underwater")

# ratio deuda/floor (loan-to-floor) distribución
d["debt_to_floor"] = d["debt_sol"] / d["floor_p15_sol"]
print("\ndebt/floor (LTV efectivo al default) describe:")
print(d["debt_to_floor"].replace([float('inf')], pd.NA).dropna().describe().to_string())

# chart: barras de sensibilidad + histograma debt/floor
gdf = pd.DataFrame(grid, columns=["floor", "interes", "pct"])
fig = go.Figure()
for fname in gdf["floor"].unique():
    sub = gdf[gdf.floor == fname]
    fig.add_bar(x=sub["interes"], y=sub["pct"], name=fname,
                text=[f"{v:.0f}%" for v in sub["pct"]], textposition="outside")
fig.update_layout(
    title="Sharky.fi — % de defaults UNDERWATER según supuestos<br>"
          f"<sub>{n} defaults con floor estimable · Dune sharky_solana + ME/Tensor · 2026-07-10</sub>",
    barmode="group", template="plotly_white",
    yaxis=dict(title="% underwater", range=[0, 100]),
    xaxis=dict(title="Supuesto de deuda (principal + interés)"),
    legend=dict(title="Método de floor", orientation="h", y=-0.25), height=520,
)
fig.write_html("reports/sharky_fase2_underwater.html")
print("\nchart -> reports/sharky_fase2_underwater.html")

# guardar dataset clasificado
d.to_csv("data/sharky_defaults_clasificados.csv", index=False)
print("dataset -> data/sharky_defaults_clasificados.csv")
