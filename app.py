# ---------------------------------
# SEA International Trade Dashboard
# ---------------------------------
# Required libraries
import os
import glob
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc

# -------------------------------
# Load & merge data
# -------------------------------
FOLDER_PATH = "data"
file_list = glob.glob(os.path.join(FOLDER_PATH, "*.csv"))
dfs = [pd.read_csv(fp) for fp in file_list]
sea_data = pd.concat(dfs, ignore_index=True)

# Clean the data
sea_data = sea_data.dropna(axis=0, how="any")

# Renaming columns
sea_data.columns = [
    "country", "country_code", "partner_name", "partner_name_code",
    "year", "export_USD", "import_USD", "trade_balance_USD"
]

# Coerce types (Convert character columns to factors)
sea_data["year"] = pd.to_numeric(sea_data["year"], errors="coerce").astype(int)
for col in ["country", "country_code", "partner_name", "partner_name_code"]:
    sea_data[col] = sea_data[col].astype("category")

# Colors for each corresponding country
COUNTRY_COLORS = {
    "Malaysia": "#77DD77",
    "Indonesia": "#FFFF99",
    "Singapore": "#B19CD9",
    "Thailand": "#FF6961",
}

# Countries order
priority = ["Malaysia", "Indonesia", "Singapore", "Thailand"]
others = [c for c in sea_data["country"].cat.categories if c not in priority]
COUNTRY_CHOICES = priority + others

# Year settings
YEAR_MIN = int(sea_data["year"].min())
YEAR_MAX = int(sea_data["year"].max())
YEAR_MIN = min(YEAR_MIN, 2015)
YEAR_MAX = max(YEAR_MAX, 2022)

# -------------------------------
# UI Layout
# -------------------------------
# App & theme
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.COSMO,
        "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css",  # bootstrap icons
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css"      # font awesome icons
    ],
    title="SEA International Trade Dashboard",
)
server = app.server

# Header with logo + link, toggle button, title
header = dbc.Navbar(
    dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(
                        html.A(
                            html.Img(
                                src="/assets/msrsb_logo.png",
                                style={
                                    "height": "42px",
                                    "width": "auto",
                                    "borderRadius": "8px"
                                },
                            ),
                            href="https://mediasmart.my/v2/main-page/",
                            target="_blank",
                            style={"textDecoration": "none"}
                        ),
                        width="auto",
                    ),
                    dbc.Col(
                        dbc.Button(
                            "☰",  
                            id="sidebar-toggle",
                            color="light",
                            outline=True,
                            size="sm",
                            className="ms-3",
                        ),
                        width="auto",
                        className="d-flex align-items-center",
                    ),
                ],
                className="g-0 align-items-center",
            ),
            # Title
            dbc.NavbarBrand(
                "SEA International Trade Dashboard",
                className="fw-bold",
                style={"fontSize": "1.3rem", "color": "white"}
            ),
        ],
        fluid=True,
    ),
    color="primary",
    dark=True,
    className="mb-3",
)

# Sidebar
sidebar = dbc.Collapse(
    dbc.Card(
        dbc.CardBody(
            [
                html.H6("Settings", className="fw-bold"),
                dcc.Dropdown(
                    id="selected_country",
                    options=[{"label": c, "value": c} for c in COUNTRY_CHOICES],
                    value="Malaysia",
                    clearable=False,
                    className="mb-3",
                    style={"zIndex": 1050},
                ),
                dcc.Slider(
                    id="selected_year",
                    min=YEAR_MIN,
                    max=YEAR_MAX,
                    step=1,
                    value=YEAR_MAX,
                    marks={y: str(y) for y in range(YEAR_MIN, YEAR_MAX + 1)},
                    className="mb-1",
                ),
                html.Div(id="year_label", className="text-muted small mb-2"),
            ],
            style={"overflow": "visible"}
        ),
        className="shadow-sm",
        style={"position": "sticky", "top": "1rem", "overflow": "visible"},
    ),
    id="sidebar",
    is_open=False,
    className="collapse",
)

# KPI cards style
def kpi_card(id_value, label, icon_class, color):
    return dbc.Card(
        dbc.CardBody(
            dbc.Row(
                [
                    # Left side: Value + Label
                    dbc.Col(
                        [
                            html.H4(id=id_value, className="mb-0 fw-bold"),
                            html.Small(label, className="text-muted"),
                        ],
                        align="center",
                    ),
                    # Right side: Icon
                    dbc.Col(
                        html.Div(
                            className=icon_class,
                            style={
                                "fontSize": "2.5rem",
                                "opacity": 0.8,
                                "color": f"var(--bs-{color})"
                            },
                        ),
                        width="auto",
                        align="center",
                    ),
                ],
                className="g-2 justify-content-between",
            )
        ),
        className=f"border-0 shadow-sm bg-{color} bg-opacity-25",
        style={"borderLeft": f"4px solid var(--bs-{color})"},
    )

# Tabs content
tabs = dcc.Tabs(
    id="tabs",
    value="trade_trends",
    children=[
        # Tab 1
        dcc.Tab(label="Trade Trends Overview", value="trade_trends", children=[
            dbc.Row([
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody([
                            html.H5("Total Trade Value Comparison Across SEA", className="card-title"),
                            dcc.Graph(id="chart_a")
                        ])
                    ), md=6
                ),
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody([
                            html.H5("Trade Balance Value Across SEA", className="card-title"),
                            dcc.Graph(id="chart_b")
                        ])
                    ), md=6
                ),
            ], className="gy-3"),
        ]),
        # Tab 2
        dcc.Tab(label="Specific Trade Trends", value="specific_trends", children=[
            dbc.Row([
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody([
                            html.H5("Export vs Import Trends", className="card-title"),
                            dcc.Graph(id="chart_c")
                        ])
                    ), md=6
                ),
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody([
                            html.H5("Export vs Import Correlation Relationship", className="card-title"),
                            dcc.Graph(id="chart_d")
                        ])
                    ), md=6
                ),
            ], className="gy-3"),
        ]),
        # Tab 3
        dcc.Tab(label="SEA Trade Data", value="table_data", children=[
            dbc.Row([
                dbc.Col(kpi_card("total_trade", "Total Trade Value (USD)", "fas fa-dollar-sign", "primary"), md=3),
                dbc.Col(kpi_card("total_export", "Total Exports (USD)", "fas fa-arrow-up", "success"), md=3),
                dbc.Col(kpi_card("total_import", "Total Imports (USD)", "fas fa-arrow-down", "danger"), md=3),
                dbc.Col(kpi_card("trade_balance", "Trade Balance (USD)", "fas fa-balance-scale", "secondary"), md=3),
            ], className="gy-3"),
            html.Br(),
            dbc.Row([
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody([
                            html.H5(id="chart_e_title", className="card-title"),
                            dash_table.DataTable(
                                id="chart_e",
                                page_size=12,
                                style_table={"overflowX": "auto"},
                                style_cell={
                                    "fontFamily": "Inter, system-ui", 
                                    "fontSize": "14px",
                                    "textAlign": "center"},
                                sort_action="native",
                                filter_action="native",
                            )
                        ])
                    ), md=12
                ),
            ], className="gy-3"),
            html.Br(),
            dbc.Row([
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody([
                            html.H5("Top Trading Partners for SEA Countries", className="card-title"),
                            dcc.Graph(id="chart_f")
                        ])
                    ), md=12
                ),
            ], className="gy-3"),
        ]),
        # Tab 4
        dcc.Tab(label="SEA Trade Contribution", value="trade_contribution", children=[
            dbc.Row([
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody([
                            html.H5("International Trade Contribution Map", className="card-title"),
                            dcc.Graph(id="chart_g")
                        ])
                    ), md=12
                ),
            ], className="gy-3"),
        ]),
    ],
)

# Dashboard layout
app.layout = dbc.Container(
    [
        header,
        dbc.Row(
            [
                # Sidebar column
                dbc.Col(
                    sidebar,
                    id="sidebar-col",
                    md=3,
                    className="d-none"  # hidden at start
                ),

                # Main content column
                dbc.Col(
                    tabs,
                    id="main-col",
                    md=12
                ),
            ],
            className="gx-3"
        ),
    ],
    fluid=True,
)

# -------------------------------
# Callbacks
# -------------------------------
# Sidebar toggle
@app.callback(
    Output("year_label", "children"),
    Input("selected_year", "value")
)
def show_year(y):
    return f"Selected Year: {y}"

@app.callback(
    [
        Output("sidebar", "is_open"),
        Output("sidebar-col", "className"),
        Output("main-col", "md"),
    ],
    Input("sidebar-toggle", "n_clicks"),
    State("sidebar", "is_open"),
)
def toggle_sidebar(n, is_open):
    if n:
        new_state = not is_open
        if new_state:  # sidebar visible
            return True, "", 9
        else:          # sidebar hidden
            return False, "d-none", 12
    # default state    
    return is_open, "d-none", 12

# Chart A: Grouped Bar Chart by Country and Year
@app.callback(
    Output("chart_a", "figure"),
    Input("selected_year", "value")
)
def chart_a(_):
    df = (
        sea_data[sea_data["country"].isin(["Malaysia", "Indonesia", "Singapore", "Thailand"])]
        .groupby(["country", "year"], as_index=False)
        .agg(trade_value=("export_USD", "sum"))
    )
    # add import
    imp = sea_data[sea_data["country"].isin(["Malaysia", "Indonesia", "Singapore", "Thailand"])] \
        .groupby(["country", "year"], as_index=False)["import_USD"].sum()
    df = df.merge(imp, on=["country", "year"], how="left")
    df["trade_value"] = df["trade_value"] + df["import_USD"]
    df["country"] = pd.Categorical(df["country"], categories=["Malaysia", "Indonesia", "Singapore", "Thailand"], ordered=True)

    fig = px.bar(
        df, x="year", y="trade_value", color="country", custom_data=["country"],
        title="Grouped Bar Chart for Total Trade Value by Country and Year",
        barmode="group",
        category_orders={"country": ["Malaysia", "Indonesia", "Singapore", "Thailand"]},
        color_discrete_map=COUNTRY_COLORS
    )
    fig.update_layout(xaxis_title="Year", yaxis_title="Total Trade Value (USD)", legend_title_text="Country")
    fig.update_traces(
        hovertemplate="<b>Country:</b> %{customdata[0]}<br>" + 
                      "<b>Year:</b> %{x}<br>" +
                      "<b>Total Trade Value:</b> %{y:,.0f} USD<extra></extra>")
    return fig

# Chart B: Heatmap of trade balance across SEA
@app.callback(
    Output("chart_b", "figure"),
    Input("selected_year", "value")
)
def chart_b(_):
    df = sea_data.groupby(["year", "country"], as_index=False)["trade_balance_USD"].sum()
    df["country"] = pd.Categorical(
        df["country"], categories=["Malaysia", "Indonesia", "Singapore", "Thailand"], ordered=True
    )

    fig = px.imshow(
        df.pivot(index="country", columns="year", values="trade_balance_USD").sort_index(),
        origin="lower",
        aspect="auto",
        title="Heatmap of Trade Balance by Country and Year",
        labels=dict(x="Year", y="Country", color="Trade Balance"),
        color_continuous_scale=[(0, "#FF6961"), (0.5, "#FFFF99"), (1, "#77DD77")]
    )
    fig.update_traces(
        hovertemplate="<b>Country:</b> %{y}<br>" +
                      "<b>Year:</b> %{x}<br>" +
                      "<b>Trade Balance:</b> %{z:,.0f} USD<extra></extra>",
        hoverlabel=dict(
            bgcolor="rgba(255, 245, 230, 0.9)",
            font_size=13,
            font_family="Inter, sans-serif",
            font_color="black",
            bordercolor="#FF8800"
        )
    )
    return fig

# Chart C: Export vs Import Trend lines for selected country
@app.callback(
    Output("chart_c", "figure"),
    Input("selected_country", "value")
)
def chart_c(country):
    plot_df = (
        sea_data[sea_data["country"] == country]
        .groupby("year", as_index=False)
        .agg(import_USD=("import_USD", "sum"), export_USD=("export_USD", "sum"))
    )
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=plot_df["year"], y=plot_df["export_USD"], mode="lines", name="Export",
                             hovertemplate="<b>Year:</b> %{x}<br>" +
                                           "<b>Export Value:</b> %{y:,.0f} USD<extra></extra>"))
    fig.add_trace(go.Scatter(x=plot_df["year"], y=plot_df["import_USD"], mode="lines", name="Import",
                             hovertemplate="<b>Year:</b> %{x}<br>" +
                                           "<b>Import Value:</b> %{y:,.0f} USD<extra></extra>"))
    fig.update_layout(title=f"Export vs Import Trend Line for {country}",
                      xaxis_title="Year", yaxis_title="Trade Value (USD)")
    return fig

# Chart D: Scatter PLot Export vs Import with regression line for selected year & country
@app.callback(
    Output("chart_d", "figure"),
    [Input("selected_country", "value"), Input("selected_year", "value")]
)
def chart_d(country, year):
    df = sea_data[(sea_data["country"] == country) & (sea_data["year"] == year)]
    fig = px.scatter(
        df, x="export_USD", y="import_USD",
        title=f"Export vs Import for {country} in {year}",
        opacity=0.9
    )
    fig.update_traces(
        selector=dict(mode="markers"),
        hovertemplate="<b>Export Value:</b> %{x:,.0f} USD<br>" +
                      "<b>Import Value:</b> %{y:,.0f} USD<extra></extra>")
    # Add OLS trendline via numpy
    if len(df) >= 2:
        x = df["export_USD"].astype(float)
        y = df["import_USD"].astype(float)
        b1, b0 = np.polyfit(x, y, 1)  # y = b1*x + b0
        xs = np.linspace(x.min(), x.max(), 100)
        ys = b1 * xs + b0
        fig.add_trace(go.Scatter(
            x=xs, y=ys, mode="lines", name="OLS fit",
            line=dict(color="#2E8BE8", width=2),
            hovertemplate="<b>OLS Fit Line</b><br>" +
                          "Import ≈ %{y:,.0f} USD when Export = %{x:,.0f} USD<extra></extra>"))
    fig.update_traces(marker=dict(color=COUNTRY_COLORS.get(country, "#1F77B4")))
    fig.update_layout(xaxis_title="Export (USD)", yaxis_title="Import (USD)")
    return fig

# Value Boxes: KPIs
@app.callback(
    [Output("total_trade", "children"),
     Output("total_export", "children"),
     Output("total_import", "children"),
     Output("trade_balance", "children")],
    [Input("selected_country", "value"), Input("selected_year", "value")]
)
def kpis(country, year):
    df = sea_data[(sea_data["country"] == country) & (sea_data["year"] == year)]
    total_trade = (df["export_USD"] + df["import_USD"]).sum()
    total_export = df["export_USD"].sum()
    total_import = df["import_USD"].sum()
    trade_balance = (df["export_USD"] - df["import_USD"]).sum()

    fmt = lambda v: f"{int(v):,}"
    return fmt(total_trade), fmt(total_export), fmt(total_import), fmt(trade_balance)

# Chart E: Full filtered data table by country
@app.callback(
    [Output("chart_e", "data"),
     Output("chart_e", "columns"),
     Output("chart_e_title", "children")],
    [Input("selected_country", "value"),
     Input("selected_year", "value")]
)
def update_table(country, year):
    filt = sea_data[(sea_data["country"] == country) & (sea_data["year"] == year)]
    tbl = filt[["country", "partner_name", "year", "export_USD", "import_USD"]].copy()
    tbl["trade_value"] = tbl["export_USD"] + tbl["import_USD"]

    # Define readable column headers
    columns = [
        {"name": "Country", "id": "country"},
        {"name": "Trading Partner", "id": "partner_name"},
        {"name": "Year", "id": "year"},
        {"name": "Export (USD)", "id": "export_USD"},
        {"name": "Import (USD)", "id": "import_USD"},
        {"name": "Total Trade (USD)", "id": "trade_value"},
    ]
    data = tbl.to_dict("records")
    title = f"Full International Trade Data for {country} in {year}"
    return data, columns, title

# Chart F: Top 10 Partners Bar Chart
@app.callback(
    Output("chart_f", "figure"),
    [Input("selected_country", "value"),
     Input("selected_year", "value")]
)
def update_top_partners(country, year):
    filt = sea_data[(sea_data["country"] == country) & (sea_data["year"] == year)]

    # Aggregate trade values
    top_export = (
        filt.groupby("partner_name", as_index=False)["export_USD"].sum()
        .rename(columns={"export_USD": "total_export"})
    )
    top_import = (
        filt.groupby("partner_name", as_index=False)["import_USD"].sum()
        .rename(columns={"import_USD": "total_import"})
    )
    top = top_export.merge(top_import, on="partner_name", how="left")
    top["total_trade"] = top["total_export"] + top["total_import"]
    top = top.sort_values("total_trade", ascending=False).head(10)
    fig = px.bar(
        top, x="total_trade", y="partner_name", orientation="h",
        title=f"Top 10 Trading Partners for {country} in {year}",
        color_discrete_sequence=[COUNTRY_COLORS.get(country, "#1F77B4")]
    )
    fig.update_traces(
        hovertemplate="<b>Trading Partner:</b> %{y}<br>" +
                      "<b>Total Trade:</b> %{x:,.0f} USD<extra></extra>")
    fig.update_layout(
        xaxis_title="Total Trade Value (USD)", yaxis_title="Partner Country"
    )
    return fig

# Chart G:  Partner trade map for selected country and year
@app.callback(
    Output("chart_g", "figure"),
    [Input("selected_country", "value"),
     Input("selected_year", "value")]
)
def chart_g(country, year):
    filtered_data = sea_data[(sea_data["country"] == country) & (sea_data["year"] == year)]
    partner_trade = (
        filtered_data.groupby("partner_name", as_index=False)
        .agg(
            total_export=("export_USD", "sum"),
            total_import=("import_USD", "sum")
        )
    )
    partner_trade["total_trade"] = partner_trade["total_export"] + partner_trade["total_import"]

    fig = px.choropleth(
        partner_trade,
        locations="partner_name",
        locationmode="country names",
        color="total_trade",
        hover_name="partner_name",
        color_continuous_scale="YlOrRd"
    )
    fig.update_traces(
        marker=dict(opacity=0.9, line=dict(width=0.3, color="black")),
        hovertemplate="<b>Trading partner:</b> %{hovertext}<br>" +
                      "<b>Total trade:</b> %{z:,.0f} USD<br>" +
                      "<extra></extra>",
        hoverlabel=dict(
            bgcolor="rgba(255, 245, 230, 0.9)",
            font_size=13,
            font_family="Inter, sans-serif",
            font_color="black",
            bordercolor="#FF8800"
        ),
        hovertext=partner_trade["partner_name"]
    )
    fig.update_geos(
        projection_type="natural earth",
        showland=True,
        landcolor="#f5f5f2",
        showocean=True,
        oceancolor="#c9e6ff",
        showcountries=True,
        countrycolor="#b0b0b0",
        showcoastlines=True,
        coastlinecolor="#8c8c8c",
        showlakes=True,
        lakecolor="#c9e6ff",
        showframe=False,
        fitbounds="locations"
    )
    fig.update_layout(
        title={
        "pad": {"t": 40},
        "text": f"International Choropleth Map for {country}’s Trade Contribution in {year}",
        "x": 0.434
        },
        coloraxis_colorbar=dict(title="Total Trade (USD)"),
        paper_bgcolor="#f8f9fa",
        plot_bgcolor="#f8f9fa",
        margin={"t":40, "r":0, "l":0, "b":0}
    )
    return fig

# -------------------------------
# Run Dash Dashboard
# -------------------------------
if __name__ == "__main__":
    app.run(debug=True, port=8051)
