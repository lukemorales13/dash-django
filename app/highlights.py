import pandas as pd
import numpy as np
import plotly.graph_objects as go

def highlight_Prestamos(df_prestamos):
    if df_prestamos.empty or 'mes_anio' not in df_prestamos.columns:
        prestamos_act = 0
        show_delta = False
    else:
        meses=list(df_prestamos['mes_anio'].unique())
        
        if len(meses) < 2:
            prestamos_act = 0
            show_delta = False
        else:
            prestamos = df_prestamos['mes_anio'].value_counts()

            prestamos = prestamos.astype(int)

            prestamos_act = int(prestamos.iloc[0])
            prestamos_ant = int(prestamos.iloc[1])

            referencia=prestamos_ant if prestamos_ant != 0 else 1
            show_delta=True

    indicador=go.Indicator(
            mode="number+delta" if show_delta else "number",
            value=prestamos_act,
            number={'valueformat': ',', 'font': {'size': 25}},
            delta={'reference': referencia, 
                'relative': True,
                'valueformat': '.1%',
                'increasing': {'color': "green"},
                'decreasing': {'color': "red"}},
            title={"text": "Préstamos Otorgados", 'font': {'size': 18}},
            domain={'x': [0.0, 0.25], 'y': [0, 1]}
    )

    return indicador

def highlight_intereses(df_intereses):
    if df_intereses.empty or 'mes_anio' not in df_intereses.columns:
        prom_ult_mes = 0
        show_delta = False
    else:
        meses=list(df_intereses['mes_anio'].unique())
        
        if len(meses) < 2:
            prom_ult_mes = 0
            show_delta = False
        else:
            pen_mes = df_intereses[df_intereses['mes_anio']==meses[1]]
            ult_mes = df_intereses[df_intereses['mes_anio']==meses[0]]

            prom_pen_mes = np.mean(pen_mes['tasa_interes'])
            prom_ult_mes = np.mean(ult_mes['tasa_interes'])
            
            referencia=prom_pen_mes if prom_pen_mes != 0 else 1
            show_delta=True

    indicador=go.Indicator(
        mode="number+delta" if show_delta else "number",
        value=prom_ult_mes,
        number={'suffix': "%", 'font': {'size': 25}},
        delta={
            'reference': referencia,
            'relative': True,
            'valueformat': '.1%',
            'increasing': {'color': "green"},
            'decreasing': {'color': "red"}
        },
        title={"text": "Tasa de Interés Prom.", 'font': {'size': 18}},
        domain={'x': [0.25, 0.50], 'y': [0, 1]}
    )
    
    return indicador        

def highlight_ganancia(df_ganancia):
    referencia = 1
    if df_ganancia.empty or 'mes_anio' not in df_ganancia.columns:
        rec_ult_mes = 0
        show_delta = False
    else:
        meses=list(df_ganancia['mes_anio'].unique())
        
        if len(meses) < 2:
            rec_ult_mes = 0
            show_delta = False
        else:
            df_ganancia['duracion_prestamo']=df_ganancia['duracion_prestamo'].str.replace(' meses','').astype(int)

            df_ganancias_ult_mes = df_ganancia[df_ganancia['mes_anio']==meses[0]].copy()
            df_ganancias_pen_mes = df_ganancia[df_ganancia['mes_anio']==meses[1]].copy()

            for index, row in df_ganancias_ult_mes.iterrows():
                if pd.notna(row['hardship_last_payment_amount']) and row['hardship_last_payment_amount'] != 0:
                    if pd.notna(row['orig_projected_additional_accrued_interest']) and pd.notna(row['hardship_length']) and row['hardship_length'] != 0:
                        ganancia = row['orig_projected_additional_accrued_interest'] / row['hardship_length']
                    else:
                        ganancia = 0    
                else:
                    ganancia = (row['loan_amnt'] * (row['tasa_interes'] / 100)) / row['duracion_prestamo']
                
                df_ganancias_ult_mes.loc[index, 'ganancia_mensual'] = ganancia

            for index, row in df_ganancias_pen_mes.iterrows():
                if pd.notna(row['hardship_last_payment_amount']) and row['hardship_last_payment_amount'] != 0:
                    if pd.notna(row['orig_projected_additional_accrued_interest']) and pd.notna(row['hardship_length']) and row['hardship_length'] != 0:
                        ganancia = row['orig_projected_additional_accrued_interest'] / row['hardship_length']
                    else:
                        ganancia = 0    
                else:
                    ganancia = (row['loan_amnt'] * (row['tasa_interes'] / 100)) / row['duracion_prestamo']
                
                df_ganancias_pen_mes.loc[index, 'ganancia_mensual'] = ganancia

            rec_ult_mes=df_ganancias_ult_mes['ganancia_mensual'].sum()
            rec_pen_mes=df_ganancias_pen_mes['ganancia_mensual'].sum()

            referencia=rec_pen_mes if rec_pen_mes != 0 else 1
            show_delta=True

    indicador=go.Indicator(
        mode="number+delta" if show_delta else "number",
        value=rec_ult_mes,
        number={'prefix': "$", 'valueformat': ',.2f', 'font': {'size': 25}},
        delta={
            'reference': referencia,
            'relative': True,
            'valueformat': '.1%',
            'increasing': {'color': "green"},
            'decreasing': {'color': "red"}
        },
        title={"text": f" Recaudación Estimada", 'font': {'size': 18}},
        domain={'x': [0.50, 0.75], 'y': [0, 1]}
    )

    return indicador

def highlight_morosos(df_morosos):
    tipos = ['Charged Off', 'Default', 'Late (31-120 days)', 'Late (16-30 days)']
    
    if df_morosos.empty or 'mes_anio' not in df_morosos.columns or 'loan_status' not in df_morosos.columns:
        valor = 0
        show_delta = False
    else:
        df_morosos = df_morosos.copy()
        df_morosos['mes_anio'] = pd.to_datetime(df_morosos['mes_anio'], errors='coerce')
        meses_morosos = sorted(df_morosos['mes_anio'].dropna().unique())

        if len(meses_morosos) < 2:
            valor = 0
            show_delta = False
        else:
            morosos_ult_mes = df_morosos[(df_morosos['mes_anio'] == meses_morosos[1]) &
                                         (df_morosos['loan_status'].isin(tipos))]
            morosos_pen_mes = df_morosos[(df_morosos['mes_anio'] == meses_morosos[0]) &
                                         (df_morosos['loan_status'].isin(tipos))]

            total_morosos_ult = len(morosos_ult_mes)
            total_morosos_pen = len(morosos_pen_mes)

            valor = total_morosos_ult
            referencia = total_morosos_pen if total_morosos_pen != 0 else 1 
            show_delta = True

    indicador = go.Indicator(
        mode="number+delta" if show_delta else "number",
        value=valor,
        number={'valueformat': ',', 'font': {'size': 25}},
        delta={
            'reference': referencia,
            'relative': True,
            'valueformat': '.1%',
            'increasing': {'color': "red"},
            'decreasing': {'color': "green"}
        } if show_delta else None,
        title={"text": "Morosos", 'font': {'size': 18}},
        domain={'x': [0.75, 1.0], 'y': [0, 1]}
    )

    return indicador 

def highlights(filtros, collectionPrestamos, collectionMorosos, collectionGanancia):
    # Generamos las consultas
    consulta = {}
    if 'region' in filtros and filtros['region']:
        consulta['estado_completo'] = {'$in': filtros['region']}
    if 'tipo_propiedad' in filtros and filtros['tipo_propiedad']:
        consulta['tipo_propiedad'] = {'$in': filtros['tipo_propiedad']}
    if 'duracion' in filtros and filtros['duracion']:
        duraciones = [d.strip() + " meses" if "meses" not in d else d.strip() for d in filtros['duracion']]
        consulta['duracion_prestamo'] = {'$in': duraciones}

    pipeline=[{"$match":consulta}]

    ult_meses = pd.DataFrame(list(collectionPrestamos.aggregate(pipeline)))
    ganancias = pd.DataFrame(list(collectionGanancia.aggregate(pipeline)))
    morosos = pd.DataFrame(list(collectionMorosos.aggregate(pipeline)))
    
    fig= go.Figure()

    high_pres=highlight_Prestamos(ult_meses)
    high_int=highlight_intereses(ult_meses)
    high_mor = highlight_morosos(morosos)
    high_rec = highlight_ganancia(ganancias)

    
    fig.add_trace(high_pres)
    fig.add_trace(high_mor)
    fig.add_trace(high_int)
    fig.add_trace(high_rec)
    
    #Estilo de los highlights
    fig.add_shape(
        type="rect",
        x0=0.01, x1=0.24,
        y0=0.25, y1=0.80,
        xref="paper", yref="paper",
        fillcolor="rgba(0,0,0,0.05)",  
        line=dict(color="rgba(0,0,0,0.2)", width=1),
        layer="below"
    )

    fig.add_layout_image(
    dict(
        source="https://img.icons8.com/badges/48/stock-share.png", 
        xref="paper", yref="paper",
        x=0.12, y=0.95,  
        sizex=0.25, sizey=0.20,
        xanchor="center", yanchor="middle",
        layer="above"
        )
    )

    fig.add_layout_image(
    dict(
        source="https://img.icons8.com/badges/48/collectibles.png", 
        xref="paper", yref="paper",
        x=0.87, y=0.95,  
        sizex=0.25, sizey=0.20,
        xanchor="center", yanchor="middle",
        layer="above"
        )
    )
    
    fig.add_shape(
        type="rect",
        x0=0.26, x1=0.49,
        y0=0.25, y1=0.8,
        xref="paper", yref="paper",
        fillcolor="rgba(0,0,0,0.05)",  
        line=dict(color="rgba(0,0,0,0.2)", width=1),
        layer="below"
    )

    fig.add_layout_image(
    dict(
        source="https://img.icons8.com/badges/48/dividends.png", 
        xref="paper", yref="paper",
        x=0.37, y=0.95,  
        sizex=0.25, sizey=0.20,
        xanchor="center", yanchor="middle",
        layer="above"
       )
    )

    fig.add_shape(
        type="rect",
        x0=0.51, x1=0.74,
        y0=0.25, y1=0.8,
        xref="paper", yref="paper",
        fillcolor="rgba(0,0,0,0.05)",  
        line=dict(color="rgba(0,0,0,0.2)", width=1),
        layer="below"
    )

    fig.add_layout_image(
    dict(
        source="https://img.icons8.com/badges/48/investment.png", 
        xref="paper", yref="paper",
        x=0.62, y=0.95,  
        sizex=0.25, sizey=0.20,
        xanchor="center", yanchor="middle",
        layer="above"
        )
    )
    
    fig.add_shape(
        type="rect",
        x0=0.76, x1=0.99,
        y0=0.25, y1=0.8,
        xref="paper", yref="paper",
        fillcolor="rgba(0,0,0,0.05)",  
        line=dict(color="rgba(0,0,0,0.2)", width=1),
        layer="below"
    )


    fig.update_layout(
        title={
        'text': "Comparativa Mensual de Indicadores Financieros",
        'y':0.95,
        'x':0.5,
        'xanchor': 'center',
        'yanchor': 'top',
        'font': dict(size=20)
        },
        paper_bgcolor="white",
        height=250,
        margin=dict(t=50, b=10, l=10, r=10)
    )

    return fig    