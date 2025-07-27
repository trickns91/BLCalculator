import streamlit as st
import pandas as pd

# Carregar ranking consolidado
df = pd.read_csv("ranking.csv")
df = df.dropna(subset=["player", "value_score"]).copy()
df["player_display"] = df["player"] + " (" + df["position_rank"] + ")"

# Adicionar picks manuais
df_picks = pd.DataFrame({
    "player": [
        "2026 1.01-1.03", "2026 1.04-1.06", "2026 1.07-1.12",
        "2026 Early 2nd", "2026 Late 2nd", "2026 Early 3rd", "2026 Late 3rd",
        "2027 1.01-1.03", "2027 1.04-1.06", "2027 1.07-1.12",
        "2027 Early 2nd", "2027 Late 2nd", "2027 Early 3rd", "2027 Late 3rd"
    ],
    "value_score": [49, 42, 35, 25, 18, 10, 6, 53, 45, 35, 24, 17, 8, 4],
    "position": ["PICK"] * 14,
    "position_rank": ["PICK"] * 14
})
df_picks["player_display"] = df_picks["player"]
df = pd.concat([df, df_picks], ignore_index=True)

# Parâmetros
pesos_ordem = [1.0, 0.85, 0.7, 0.55, 0.4]
pesos_status = {"Titular": 1.0, "Reserva": 0.6}

st.set_page_config(page_title="Calculadora de Trade Dynasty", layout="wide")
st.title("🤝 Calculadora de Trade - Fantasy Dynasty")

st.caption("Selecione jogadores ou digite nomes manualmente, incluindo picks. Avaliaremos impacto relativo com base em score ponderado.")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Lado A")
    jogadores_a = []
    for i in range(5):
        nome = st.text_input(f"Jogador ou Pick {i+1} (A)", key=f"nome_a_{i}")
        if nome:
            status = st.radio("Status", ["Titular", "Reserva"], key=f"status_a_{i}", horizontal=True)
            jogadores_a.append((nome.strip().lower(), status))

with col2:
    st.subheader("Lado B")
    jogadores_b = []
    for i in range(5):
        nome = st.text_input(f"Jogador ou Pick {i+1} (B)", key=f"nome_b_{i}")
        if nome:
            status = st.radio("Status", ["Titular", "Reserva"], key=f"status_b_{i}", horizontal=True)
            jogadores_b.append((nome.strip().lower(), status))

st.divider()

@st.cache_data
def calcular_valor(jogadores):
    total = 0
    detalhes = []
    for i, (nome, status) in enumerate(jogadores):
        row = df[df["player"].str.lower() == nome]
        if row.empty:
            detalhes.append((f"{nome} (Não encontrado)", 0))
            continue
        score = row.iloc[0]["value_score"]
        peso_ordem = pesos_ordem[i] if i < len(pesos_ordem) else 0.25
        peso_status = pesos_status[status]
        valor = score * peso_ordem * peso_status
        total += valor
        detalhes.append((row.iloc[0]["player_display"], round(valor, 2)))
    return round(total, 2), detalhes

valor_a, detalhes_a = calcular_valor(jogadores_a)
valor_b, detalhes_b = calcular_valor(jogadores_b)

col1, col2 = st.columns(2)
with col1:
    st.metric("Total lado A", valor_a)
    for nome, v in detalhes_a:
        st.write(f"{nome} → {v}")

with col2:
    st.metric("Total lado B", valor_b)
    for nome, v in detalhes_b:
        st.write(f"{nome} → {v}")

st.divider()

if valor_a and valor_b:
    delta = round(abs(valor_a - valor_b), 2)
    maior = "A" if valor_a > valor_b else "B"
    menor = "B" if maior == "A" else "A"
    pct = round((delta / max(valor_a, valor_b)) * 100, 1)

    st.subheader("📊 Avaliação da Troca")
    st.write(f"**Lado {maior} leva vantagem de {delta} pontos ({pct}%) sobre o lado {menor}.**")

    candidatos = df[~df["player"].isin([x[0] for x in jogadores_a + jogadores_b])]
    candidatos["diff"] = abs(candidatos["value_score"] - delta)
    sugestoes = candidatos.sort_values("diff").head(5)
    st.markdown("**Jogadores ou picks com valor próximo do gap:**")
    st.table(sugestoes[["player", "position", "value_score"]].reset_index(drop=True))
