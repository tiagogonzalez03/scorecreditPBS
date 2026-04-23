from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import numpy as np
import os

app = Flask(__name__)
CORS(app)

def carregar_dados():
    base_path = os.path.dirname(__file__)
    file_path = os.path.join(base_path, '..', 'data', 'SPGlobal_Export_4-14-2026_FinalVersion.csv')

    df_raw = pd.read_csv(file_path, skiprows=4)
    df_raw = df_raw.iloc[1:].reset_index(drop=True)

    df = pd.DataFrame()
    df['Empresa'] = df_raw.iloc[:, 0].astype(str).apply(lambda x: x.split(' (')[0])
    df['Divida_2024'] = pd.to_numeric(df_raw.iloc[:, 3].astype(str).str.replace(',', ''), errors='coerce')
    df['EBITDA_2024'] = pd.to_numeric(df_raw.iloc[:, 9].astype(str).str.replace(',', ''), errors='coerce')

    df['Alavancagem'] = (df['Divida_2024'] / df['EBITDA_2024'].replace(0, np.nan)).round(2)

    def definir_rating(row):
        if row['EBITDA_2024'] <= 0 or pd.isna(row['Alavancagem']):
            return '🔴 CRÍTICO'
        if row['Alavancagem'] > 4.5:
            return '🔴 ALTO RISCO'
        if row['Alavancagem'] < 2.0:
            return '🟢 BAIXO RISCO'
        return '🟡 MODERADO'

    df['Rating'] = df.apply(definir_rating, axis=1)

    return df

@app.route('/api', methods=['GET'])
def api_home():
    empresa_query = request.args.get('empresa', '').lower()
    df = carregar_dados()

    if empresa_query:
        resultado = df[df['Empresa'].str.lower().str.contains(empresa_query)]
        if not resultado.empty:
            return jsonify(resultado.iloc[0].to_dict())
        return jsonify({"erro": "Empresa não encontrada"}), 404

    return jsonify({
        "status": "online",
        "mensagem": "API ativa. Use /api?empresa=NOME"
    })

# necessário pro Vercel
index = app
