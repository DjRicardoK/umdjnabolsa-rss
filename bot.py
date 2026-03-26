import datetime as dt
import locale
from telegram import Bot, InlineKeyboardMarkup, InlineKeyboardButton
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio
from zoneinfo import ZoneInfo
import logging
import re

# ================= CONFIG =================
try:
    locale.setlocale(locale.LC_TIME, "pt_BR.UTF-8")
except:
    pass

BOT_TOKEN = "7963078795:AAFAqoPOOqT-E25zGYDsk-tRZ3yNWYt5LPg"
GROUP_ID = -1002281032197
TZ = ZoneInfo("America/Sao_Paulo")
bot = Bot(token=BOT_TOKEN)

SEPARADOR = "━━━━━━━━━━━━━━━━━━━━"
FOCO_NASDAQ_OURO = True

# ================= NOVAS VARIÁVEIS =================
alertados_30 = set()
alertados_5 = set()
alerta_5_enviado = set()
alerta_dia_perigoso = set()
alerta_janela = set()
ultimo_status_cmd = None
ultimo_relatorio_semana = None
encerramento_enviado = set()

# ================= DIAS DA SEMANA =================
DIAS_SEMANA = {
    0: "Segunda Feira",
    1: "Terça Feira",
    2: "Quarta Feira",
    3: "Quinta Feira",
    4: "Sexta Feira",
    5: "Sábado",
    6: "Domingo"
}

EXPLICACOES = {

"Índice de Atividade Nacional Fed Chicago (Fev)": {
    "impacto": "🟠 ALTO",
    "descricao": "Mede a atividade econômica nacional com base em 85 indicadores. Valor acima de zero indica crescimento acima da média histórica.",
    "link": "https://www.chicagofed.org/research/data/cfnai/current-data"
},

"Gastos de Construção (Mensal) (Jan)": {
    "impacto": "🟡 MÉDIO",
    "descricao": "Variação mensal nos gastos totais de construção nos EUA. Reflete atividade no setor imobiliário e de infraestrutura.",
    "link": "https://www.census.gov/construction/c30/c30index.html"
},

"Leilão Americano Bill a 3 meses": {
    "impacto": "🔵 BAIXO",
    "descricao": "Leilão de títulos de curto prazo do Tesouro dos EUA.",
    "link": "https://www.treasurydirect.gov/auctions/announcements-data-results/"
},

"Leilão Americano Bill a 6 meses": {
    "impacto": "🔵 BAIXO",
    "descricao": "Leilão de títulos de 6 meses do Tesouro americano.",
    "link": "https://www.treasurydirect.gov/auctions/announcements-data-results/"
},

"GDPNow do Fed de Atlanta (Q1)": {
    "impacto": "🟡 MÉDIO",
    "descricao": "Projeção em tempo real do PIB do 1º trimestre pelo Federal Reserve de Atlanta.",
    "link": "https://www.atlantafed.org/cqer/research/gdpnow"
},

"Variação semanal de empregos da ADP": {
    "impacto": "🟠 ALTO",
    "descricao": "Estimativa semanal de criação de empregos no setor privado pela ADP.",
    "link": "https://adpemploymentreport.com/"
},

"Custo Unitário da Mão de Obra (Trimestral) (Q4)": {
    "impacto": "🟠 ALTO",
    "descricao": "Variação trimestral do custo por unidade de trabalho. Alta indica pressão inflacionária salarial, monitorada de perto pelo Fed.",
    "link": "https://www.bls.gov/lpc/"
},

"Produtividade do Setor Não Agrícola (Trimestral) (Q4)": {
    "impacto": "🟠 ALTO",
    "descricao": "Mede o output por hora trabalhada fora do setor agrícola. Produtividade alta permite salários maiores sem inflação.",
    "link": "https://www.bls.gov/lpc/"
},

"Índice Redbook (Anual)": {
    "impacto": "🟡 MÉDIO",
    "descricao": "Indicador semanal de vendas no varejo nos EUA.",
    "link": "https://br.investing.com/economic-calendar/redbook-915"
},

"PMI Industrial (Mar)": {
    "impacto": "🟠 ALTO",
    "descricao": "Índice de gerentes de compras do setor industrial. Acima de 50 indica expansão. Forte influência sobre Nasdaq e dólar.",
    "link": "https://www.spglobal.com/marketintelligence/en/mi/research-analysis/us-pmi.html"
},

"PMI do Setor de Serviços (Mar)": {
    "impacto": "🟠 ALTO",
    "descricao": "PMI de serviços. Setor representa ~70% do PIB americano. Impacta expectativas de crescimento e política do Fed.",
    "link": "https://www.spglobal.com/marketintelligence/en/mi/research-analysis/us-pmi.html"
},

"PMI Composto S&P Global (Mar)": {
    "impacto": "🟠 ALTO",
    "descricao": "Combinação do PMI industrial e de serviços. Visão geral da saúde econômica americana.",
    "link": "https://www.spglobal.com/marketintelligence/en/mi/research-analysis/us-pmi.html"
},

"Índice de Manufatura Fed Richmond (Mar)": {
    "impacto": "🟡 MÉDIO",
    "descricao": "Mede a atividade industrial na região de Richmond. Terceiro indicador regional do setor manufatureiro.",
    "link": "https://www.richmondfed.org/research/regional_economy/surveys_of_business_conditions/manufacturing"
},

"Índice de Embarques do Setor Industrial Richmond (Mar)": {
    "impacto": "🔵 BAIXO",
    "descricao": "Subcomponente de embarques do índice industrial Fed Richmond.",
    "link": "https://www.richmondfed.org/research/regional_economy/surveys_of_business_conditions/manufacturing"
},

"Índice do Setor de Serviços Richmond (Mar)": {
    "impacto": "🟡 MÉDIO",
    "descricao": "Atividade no setor de serviços da região de Richmond.",
    "link": "https://www.richmondfed.org/research/regional_economy/surveys_of_business_conditions/service_sector"
},

"Leilão Americano Note a 2 anos": {
    "impacto": "🟡 MÉDIO",
    "descricao": "Leilão do título de 2 anos do Tesouro americano. Taxa resultante influencia expectativas de juros de curto prazo.",
    "link": "https://www.treasurydirect.gov/auctions/announcements-data-results/"
},

"Massa Monetária (Agregado M2) (Mensal) (Fev)": {
    "impacto": "🟡 MÉDIO",
    "descricao": "Volume total de dinheiro em circulação (M2). Crescimento acelerado pode indicar pressão inflacionária futura.",
    "link": "https://www.federalreserve.gov/releases/h6/"
},

"Estoques de Petróleo Bruto Semanal API": {
    "impacto": "🟡 MÉDIO",
    "descricao": "Prévia semanal dos estoques de petróleo nos EUA divulgada pelo API.",
    "link": "https://www.api.org/products-and-services/statistics"
},

"Discurso de Barr, vice-presidente de Supervisão do Fed": {
    "impacto": "🟠 ALTO",
    "descricao": "Comentários do vice-presidente de supervisão do Fed sobre regulação bancária e política monetária.",
    "link": "https://www.federalreserve.gov/newsevents/speeches.htm"
},

"Juros de Hipotecas de 30 anos MBA": {
    "impacto": "🟡 MÉDIO",
    "descricao": "Taxa média de financiamento imobiliário de 30 anos nos EUA.",
    "link": "https://www.mba.org/news-and-research/weekly-mortgage-applications-survey"
},

"Pedidos de Hipotecas MBA (Semanal)": {
    "impacto": "🟡 MÉDIO",
    "descricao": "Volume semanal de solicitações de hipotecas.",
    "link": "https://www.mba.org/news-and-research/weekly-mortgage-applications-survey"
},

"Índice de Compras MBA": {
    "impacto": "🔵 BAIXO",
    "descricao": "Indicador de atividade de compra de imóveis financiados.",
    "link": "https://br.investing.com/economic-calendar/mba-purchase-index-1490"
},

"Índice do Mercado Hipotecário": {
    "impacto": "🔵 BAIXO",
    "descricao": "Mede a atividade total do mercado hipotecário.",
    "link": "https://br.investing.com/economic-calendar/mba-mortgage-market-index-1489"
},

"Pedidos de Refinanciamento Hipotecário": {
    "impacto": "🔵 BAIXO",
    "descricao": "Volume de refinanciamentos imobiliários.",
    "link": "https://br.investing.com/economic-calendar/mba-refinancing-index-1491"
},

"Transações Correntes (Q4)": {
    "impacto": "🟡 MÉDIO",
    "descricao": "Saldo das transações correntes dos EUA no 4º trimestre. Déficit elevado pode pressionar o dólar.",
    "link": "https://www.bea.gov/data/intl-trade-investment/international-transactions"
},

"Preços de Bens Importados (Mensal) (Fev)": {
    "impacto": "🟠 ALTO",
    "descricao": "Variação mensal nos preços dos bens importados. Indica pressão inflacionária vinda do exterior.",
    "link": "https://www.bls.gov/mxp/"
},

"Preços de Bens Exportados (Mensal) (Fev)": {
    "impacto": "🟡 MÉDIO",
    "descricao": "Variação mensal nos preços dos bens exportados pelos EUA.",
    "link": "https://www.bls.gov/mxp/"
},

"Índice de Preços de Exportação (Anual) (Fev)": {
    "impacto": "🟡 MÉDIO",
    "descricao": "Variação anual nos preços de exportação americanos.",
    "link": "https://www.bls.gov/mxp/"
},

"Índice de Preços de Importação (Anual) (Fev)": {
    "impacto": "🟠 ALTO",
    "descricao": "Variação anual nos preços de importação. Alta pode antecipar inflação ao consumidor, especialmente com tarifas.",
    "link": "https://www.bls.gov/mxp/"
},

"Estoques de Petróleo Bruto": {
    "impacto": "🟠 ALTO",
    "descricao": "Relatório oficial semanal de estoques de petróleo divulgado pela EIA.",
    "link": "https://www.eia.gov/petroleum/supply/weekly/"
},

"Estoques de Petróleo em Cushing": {
    "impacto": "🟡 MÉDIO",
    "descricao": "Volume armazenado no principal hub de petróleo dos EUA.",
    "link": "https://www.eia.gov/petroleum/supply/weekly/"
},

"Produção de Gasolina": {
    "impacto": "🟡 MÉDIO",
    "descricao": "Produção semanal de gasolina nos EUA.",
    "link": "https://www.eia.gov/petroleum/supply/weekly/"
},

"Importações de Petróleo Bruto": {
    "impacto": "🟡 MÉDIO",
    "descricao": "Volume de petróleo importado pelos EUA.",
    "link": "https://www.eia.gov/petroleum/supply/weekly/"
},

"EIA - Taxas semanais de utilização de refinarias (Semanal)": {
    "impacto": "🟡 MÉDIO",
    "descricao": "Percentual de capacidade utilizada nas refinarias americanas.",
    "link": "https://www.eia.gov/petroleum/supply/weekly/"
},

"Produção de Combustível Destilado": {
    "impacto": "🟡 MÉDIO",
    "descricao": "Produção semanal de diesel e derivados nos EUA.",
    "link": "https://www.eia.gov/petroleum/supply/weekly/"
},

"Estoques de Óleo para Aquecimento": {
    "impacto": "🔵 BAIXO",
    "descricao": "Volume armazenado de óleo de aquecimento.",
    "link": "https://www.eia.gov/petroleum/supply/weekly/"
},

"Estoques de Gasolina": {
    "impacto": "🟠 ALTO",
    "descricao": "Volume armazenado de gasolina. Impacta inflação e preço do petróleo.",
    "link": "https://www.eia.gov/petroleum/supply/weekly/"
},

"Relatório Semanal EIA de Estoques de Destilados": {
    "impacto": "🟡 MÉDIO",
    "descricao": "Variação semanal dos estoques de combustíveis destilados.",
    "link": "https://www.eia.gov/petroleum/supply/weekly/"
},

"Atividade das refinarias de Petróleo pela EIA (Semanal)": {
    "impacto": "🟡 MÉDIO",
    "descricao": "Variação semanal na atividade das refinarias americanas.",
    "link": "https://www.eia.gov/petroleum/supply/weekly/"
},

"Leilão Americano Note a 5 anos": {
    "impacto": "🟡 MÉDIO",
    "descricao": "Leilão do título de 5 anos do Tesouro americano. Influencia juros intermediários e custo do crédito.",
    "link": "https://www.treasurydirect.gov/auctions/announcements-data-results/"
},

"Pedidos Iniciais por Seguro-Desemprego": {
    "impacto": "🔴 EXTREMO",
    "descricao": "Novos pedidos de auxílio-desemprego. Mercado de trabalho fraco pode fortalecer ouro e pressionar Nasdaq.",
    "link": "https://www.dol.gov/ui/data.pdf"
},

"Pedidos Contínuos por Seguro-Desemprego": {
    "impacto": "🟠 ALTO",
    "descricao": "Número de pessoas que continuam recebendo seguro-desemprego. Indica tendência do mercado de trabalho.",
    "link": "https://www.dol.gov/ui/data.pdf"
},

"Média de Pedidos de Seguro-Desemprego (4 Semanas)": {
    "impacto": "🟡 MÉDIO",
    "descricao": "Média móvel de 4 semanas dos pedidos iniciais. Suaviza volatilidade semanal.",
    "link": "https://www.dol.gov/ui/data.pdf"
},

"Estoque de Gás Natural": {
    "impacto": "🟡 MÉDIO",
    "descricao": "Variação semanal nos estoques de gás natural nos EUA.",
    "link": "https://www.eia.gov/naturalgas/storage/dashboard/"
},

"Índice Composto Fed Kansas (Mar)": {
    "impacto": "🟡 MÉDIO",
    "descricao": "Indicador composto da atividade econômica na região do Fed de Kansas City.",
    "link": "https://www.kansascityfed.org/surveys/manfsurvey/"
},

"Índice de Atividade Industrial Fed KC (Mar)": {
    "impacto": "🟡 MÉDIO",
    "descricao": "Mede a atividade manufatureira na região do Federal Reserve de Kansas City.",
    "link": "https://www.kansascityfed.org/surveys/manfsurvey/"
},

"Leilão Americano Bill a 4 semanas": {
    "impacto": "🔵 BAIXO",
    "descricao": "Leilão de títulos de curtíssimo prazo do Tesouro dos EUA.",
    "link": "https://www.treasurydirect.gov/auctions/announcements-data-results/"
},

"Leilão Americano Bill a 8 semanas": {
    "impacto": "🔵 BAIXO",
    "descricao": "Leilão de títulos de 8 semanas do Tesouro americano.",
    "link": "https://www.treasurydirect.gov/auctions/announcements-data-results/"
},

"Leilão Americano Note a 7 anos": {
    "impacto": "🟡 MÉDIO",
    "descricao": "Leilão do título de 7 anos do Tesouro americano. Taxa resultante influencia juros de médio prazo.",
    "link": "https://www.treasurydirect.gov/auctions/announcements-data-results/"
},

"Discurso de Cook, governador do Fed": {
    "impacto": "🟠 ALTO",
    "descricao": "Comentários da governadora do Fed sobre perspectivas econômicas e política monetária.",
    "link": "https://www.federalreserve.gov/newsevents/speeches.htm"
},

"Balanço Patrimonial do Federal Reserve": {
    "impacto": "🟡 MÉDIO",
    "descricao": "Tamanho do balanço do Fed. Redução (QT) indica aperto monetário; expansão (QE) indica estímulo.",
    "link": "https://www.federalreserve.gov/releases/h41/"
},

"Saldos de reservas com bancos do Federal Reserve": {
    "impacto": "🟡 MÉDIO",
    "descricao": "Volume de reservas mantidas pelos bancos comerciais junto ao Fed. Indica liquidez do sistema bancário.",
    "link": "https://www.federalreserve.gov/releases/h41/"
},

"Discurso de Jefferson, governador do Fed": {
    "impacto": "🟠 ALTO",
    "descricao": "Comentários do vice-presidente do Fed sobre política monetária e perspectivas econômicas.",
    "link": "https://www.federalreserve.gov/newsevents/speeches.htm"
},

"Nível de Estoques do Varejo excluindo Automóveis (Fev)": {
    "impacto": "🟡 MÉDIO",
    "descricao": "Variação nos estoques do setor varejista excluindo automóveis. Componente do cálculo do PIB.",
    "link": "https://www.census.gov/retail/index.html"
},

"Expectativas de Inflação Michigan (Mar)": {
    "impacto": "🔴 EXTREMO",
    "descricao": "Expectativas de inflação para 1 ano dos consumidores americanos. Alta persistente pressiona o Fed a manter juros elevados.",
    "link": "https://data.sca.isr.umich.edu/"
},

"Confiança do Consumidor Michigan - Leitura Final (Mar)": {
    "impacto": "🟠 ALTO",
    "descricao": "Leitura final do índice de confiança do consumidor da Universidade de Michigan. Revisão da prévia divulgada semanas antes.",
    "link": "https://data.sca.isr.umich.edu/"
},

"Expectativas de Inflação a 5 anos Michigan (Mar)": {
    "impacto": "🔴 EXTREMO",
    "descricao": "Expectativas de inflação de longo prazo dos consumidores. Monitorado de perto pelo Fed como âncora das expectativas inflacionárias.",
    "link": "https://data.sca.isr.umich.edu/"
},

"Índice Michigan de Percepção do Consumidor (Mar)": {
    "impacto": "🟠 ALTO",
    "descricao": "Índice geral de sentimento do consumidor americano. Quedas indicam possível retração no consumo e no crescimento.",
    "link": "https://data.sca.isr.umich.edu/"
},

"Índice de Condições Atuais Michigan (Mar)": {
    "impacto": "🟠 ALTO",
    "descricao": "Subcomponente do Michigan que avalia as condições econômicas presentes percebidas pelo consumidor.",
    "link": "https://data.sca.isr.umich.edu/"
},

"Estoques no Atacado (Mensal) (Fev)": {
    "impacto": "🟡 MÉDIO",
    "descricao": "Nível de estoques no setor atacadista. Impacta estimativas do PIB.",
    "link": "https://www.census.gov/wholesale/index.html"
},

"Discurso de Mary Daly, Membro do FOMC": {
    "impacto": "🟠 ALTO",
    "descricao": "Comentários da presidente do Fed de São Francisco sobre política monetária. Membro votante do FOMC.",
    "link": "https://www.federalreserve.gov/newsevents/speeches.htm"
},

"Contagem de Sondas Baker Hughes": {
    "impacto": "🔵 BAIXO",
    "descricao": "Número de plataformas de petróleo e gás em operação nos EUA.",
    "link": "https://rigcount.bakerhughes.com/"
},

"Contagem Total de Sondas dos EUA por Baker Hughes": {
    "impacto": "🔵 BAIXO",
    "descricao": "Total de plataformas ativas de petróleo, gás e mistas nos EUA.",
    "link": "https://rigcount.bakerhughes.com/"
},

"S&P 500 - Posições líquidas de especuladores no relatório da CFTC": {
    "impacto": "🔵 BAIXO",
    "descricao": "Posicionamento dos grandes especuladores no S&P 500 segundo o relatório COT da CFTC.",
    "link": "https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm"
},

"Nasdaq 100 - Posições líquidas de especuladores no relatório da CFTC": {
    "impacto": "🟡 MÉDIO",
    "descricao": "Posicionamento líquido dos especuladores no Nasdaq 100. Indica sentimento institucional.",
    "link": "https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm"
},

"Ouro - Posições líquidas de especuladores no relatório da CFTC": {
    "impacto": "🟡 MÉDIO",
    "descricao": "Posicionamento líquido dos especuladores no ouro. Alta posição comprada pode indicar topo.",
    "link": "https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm"
},

"Petróleo - Posições líquidas de especuladores no relatório da CFTC": {
    "impacto": "🔵 BAIXO",
    "descricao": "Posicionamento especulativo no petróleo WTI segundo o relatório COT.",
    "link": "https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm"
},

"Alumínio: Posições líquidas de especuladores no relatório da CFTC": {
    "impacto": "🔵 BAIXO",
    "descricao": "Posicionamento especulativo no alumínio segundo o relatório COT da CFTC.",
    "link": "https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm"
},

"Cobre - Posições líquidas de especuladores no relatório da CFTC": {
    "impacto": "🔵 BAIXO",
    "descricao": "Posicionamento especulativo no cobre. Indicador de sentimento sobre crescimento global.",
    "link": "https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm"
},

"Prata - Posições líquidas de especuladores no relatório da CFTC": {
    "impacto": "🔵 BAIXO",
    "descricao": "Posicionamento especulativo na prata segundo o relatório COT.",
    "link": "https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm"
},

"Gás Natural: Posições líquidas de especuladores no relatório da CFTC": {
    "impacto": "🔵 BAIXO",
    "descricao": "Posicionamento especulativo no gás natural segundo o relatório COT.",
    "link": "https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm"
},

"Trigo: Posições líquidas de especuladores no relatório da CFTC": {
    "impacto": "🔵 BAIXO",
    "descricao": "Posicionamento especulativo no trigo segundo o relatório COT da CFTC.",
    "link": "https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm"
},

"Milho: Posições líquidas de especuladores no relatório da CFTC": {
    "impacto": "🔵 BAIXO",
    "descricao": "Posicionamento especulativo no milho segundo o relatório COT da CFTC.",
    "link": "https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm"
},

"Soja: Posições líquidas de especuladores no relatório da CFTC": {
    "impacto": "🔵 BAIXO",
    "descricao": "Posicionamento especulativo na soja segundo o relatório COT da CFTC.",
    "link": "https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm"
},

}

EVENTOS_FIXOS = [

# SEGUNDA 23/03
{"data":"2026-03-23","hora":"09:30","nome":"Índice de Atividade Nacional Fed Chicago (Fev)"},
{"data":"2026-03-23","hora":"11:00","nome":"Gastos de Construção (Mensal) (Jan)"},
{"data":"2026-03-23","hora":"12:30","nome":"Leilão Americano Bill a 3 meses"},
{"data":"2026-03-23","hora":"12:30","nome":"Leilão Americano Bill a 6 meses"},
{"data":"2026-03-23","hora":"14:00","nome":"GDPNow do Fed de Atlanta (Q1)"},

# TERÇA 24/03
{"data":"2026-03-24","hora":"09:15","nome":"Variação semanal de empregos da ADP"},
{"data":"2026-03-24","hora":"09:30","nome":"Custo Unitário da Mão de Obra (Trimestral) (Q4)"},
{"data":"2026-03-24","hora":"09:30","nome":"Produtividade do Setor Não Agrícola (Trimestral) (Q4)"},
{"data":"2026-03-24","hora":"09:55","nome":"Índice Redbook (Anual)"},
{"data":"2026-03-24","hora":"10:45","nome":"PMI Industrial (Mar)"},
{"data":"2026-03-24","hora":"10:45","nome":"PMI do Setor de Serviços (Mar)"},
{"data":"2026-03-24","hora":"10:45","nome":"PMI Composto S&P Global (Mar)"},
{"data":"2026-03-24","hora":"11:00","nome":"Índice de Manufatura Fed Richmond (Mar)"},
{"data":"2026-03-24","hora":"11:00","nome":"Índice de Embarques do Setor Industrial Richmond (Mar)"},
{"data":"2026-03-24","hora":"11:00","nome":"Índice do Setor de Serviços Richmond (Mar)"},
{"data":"2026-03-24","hora":"14:00","nome":"Leilão Americano Note a 2 anos"},
{"data":"2026-03-24","hora":"14:00","nome":"Massa Monetária (Agregado M2) (Mensal) (Fev)"},
{"data":"2026-03-24","hora":"17:30","nome":"Estoques de Petróleo Bruto Semanal API"},
{"data":"2026-03-24","hora":"19:30","nome":"Discurso de Barr, vice-presidente de Supervisão do Fed"},

# QUARTA 25/03
{"data":"2026-03-25","hora":"08:00","nome":"Juros de Hipotecas de 30 anos MBA"},
{"data":"2026-03-25","hora":"08:00","nome":"Pedidos de Hipotecas MBA (Semanal)"},
{"data":"2026-03-25","hora":"08:00","nome":"Índice de Compras MBA"},
{"data":"2026-03-25","hora":"08:00","nome":"Índice do Mercado Hipotecário"},
{"data":"2026-03-25","hora":"08:00","nome":"Pedidos de Refinanciamento Hipotecário"},
{"data":"2026-03-25","hora":"09:30","nome":"Transações Correntes (Q4)"},
{"data":"2026-03-25","hora":"09:30","nome":"Preços de Bens Importados (Mensal) (Fev)"},
{"data":"2026-03-25","hora":"09:30","nome":"Preços de Bens Exportados (Mensal) (Fev)"},
{"data":"2026-03-25","hora":"09:30","nome":"Índice de Preços de Exportação (Anual) (Fev)"},
{"data":"2026-03-25","hora":"09:30","nome":"Índice de Preços de Importação (Anual) (Fev)"},
{"data":"2026-03-25","hora":"11:30","nome":"Estoques de Petróleo Bruto"},
{"data":"2026-03-25","hora":"11:30","nome":"Estoques de Petróleo em Cushing"},
{"data":"2026-03-25","hora":"11:30","nome":"Produção de Gasolina"},
{"data":"2026-03-25","hora":"11:30","nome":"Importações de Petróleo Bruto"},
{"data":"2026-03-25","hora":"11:30","nome":"EIA - Taxas semanais de utilização de refinarias (Semanal)"},
{"data":"2026-03-25","hora":"11:30","nome":"Produção de Combustível Destilado"},
{"data":"2026-03-25","hora":"11:30","nome":"Estoques de Óleo para Aquecimento"},
{"data":"2026-03-25","hora":"11:30","nome":"Estoques de Gasolina"},
{"data":"2026-03-25","hora":"11:30","nome":"Relatório Semanal EIA de Estoques de Destilados"},
{"data":"2026-03-25","hora":"11:30","nome":"Atividade das refinarias de Petróleo pela EIA (Semanal)"},
{"data":"2026-03-25","hora":"14:00","nome":"Leilão Americano Note a 5 anos"},

# QUINTA 26/03
{"data":"2026-03-26","hora":"09:30","nome":"Pedidos Iniciais por Seguro-Desemprego"},
{"data":"2026-03-26","hora":"09:30","nome":"Pedidos Contínuos por Seguro-Desemprego"},
{"data":"2026-03-26","hora":"09:30","nome":"Média de Pedidos de Seguro-Desemprego (4 Semanas)"},
{"data":"2026-03-26","hora":"11:30","nome":"Estoque de Gás Natural"},
{"data":"2026-03-26","hora":"12:00","nome":"Índice Composto Fed Kansas (Mar)"},
{"data":"2026-03-26","hora":"12:00","nome":"Índice de Atividade Industrial Fed KC (Mar)"},
{"data":"2026-03-26","hora":"12:30","nome":"Leilão Americano Bill a 4 semanas"},
{"data":"2026-03-26","hora":"12:30","nome":"Leilão Americano Bill a 8 semanas"},
{"data":"2026-03-26","hora":"14:00","nome":"Leilão Americano Note a 7 anos"},
{"data":"2026-03-26","hora":"17:00","nome":"Discurso de Cook, governador do Fed"},
{"data":"2026-03-26","hora":"17:30","nome":"Balanço Patrimonial do Federal Reserve"},
{"data":"2026-03-26","hora":"17:30","nome":"Saldos de reservas com bancos do Federal Reserve"},
{"data":"2026-03-26","hora":"20:00","nome":"Discurso de Jefferson, governador do Fed"},
{"data":"2026-03-26","hora":"20:10","nome":"Discurso de Barr, vice-presidente de Supervisão do Fed"},

# SEXTA 27/03
{"data":"2026-03-27","hora":"09:30","nome":"Nível de Estoques do Varejo excluindo Automóveis (Fev)"},
{"data":"2026-03-27","hora":"11:00","nome":"Expectativas de Inflação Michigan (Mar)"},
{"data":"2026-03-27","hora":"11:00","nome":"Confiança do Consumidor Michigan - Leitura Final (Mar)"},
{"data":"2026-03-27","hora":"11:00","nome":"Expectativas de Inflação a 5 anos Michigan (Mar)"},
{"data":"2026-03-27","hora":"11:00","nome":"Índice Michigan de Percepção do Consumidor (Mar)"},
{"data":"2026-03-27","hora":"11:00","nome":"Índice de Condições Atuais Michigan (Mar)"},
{"data":"2026-03-27","hora":"11:00","nome":"Estoques no Atacado (Mensal) (Fev)"},
{"data":"2026-03-27","hora":"12:30","nome":"Discurso de Mary Daly, Membro do FOMC"},
{"data":"2026-03-27","hora":"14:00","nome":"Contagem de Sondas Baker Hughes"},
{"data":"2026-03-27","hora":"14:00","nome":"Contagem Total de Sondas dos EUA por Baker Hughes"},
{"data":"2026-03-27","hora":"17:30","nome":"S&P 500 - Posições líquidas de especuladores no relatório da CFTC"},
{"data":"2026-03-27","hora":"17:30","nome":"Nasdaq 100 - Posições líquidas de especuladores no relatório da CFTC"},
{"data":"2026-03-27","hora":"17:30","nome":"Ouro - Posições líquidas de especuladores no relatório da CFTC"},
{"data":"2026-03-27","hora":"17:30","nome":"Petróleo - Posições líquidas de especuladores no relatório da CFTC"},
{"data":"2026-03-27","hora":"17:30","nome":"Alumínio: Posições líquidas de especuladores no relatório da CFTC"},
{"data":"2026-03-27","hora":"17:30","nome":"Cobre - Posições líquidas de especuladores no relatório da CFTC"},
{"data":"2026-03-27","hora":"17:30","nome":"Prata - Posições líquidas de especuladores no relatório da CFTC"},
{"data":"2026-03-27","hora":"17:30","nome":"Gás Natural: Posições líquidas de especuladores no relatório da CFTC"},
{"data":"2026-03-27","hora":"17:30","nome":"Trigo: Posições líquidas de especuladores no relatório da CFTC"},
{"data":"2026-03-27","hora":"17:30","nome":"Milho: Posições líquidas de especuladores no relatório da CFTC"},
{"data":"2026-03-27","hora":"17:30","nome":"Soja: Posições líquidas de especuladores no relatório da CFTC"},

]
# ================= ALERTAS =================

def relevante_para_nasdaq_ouro(nome_evento: str) -> bool:
    palavras_chave = [
        "CPI", "IPC", "PPI", "Payroll", "NFP", "FOMC", "Fed",
        "Powell", "Juros", "Interest Rate", "Taxa",
        "Inflação", "PIB", "GDP", "Desemprego", "Unemployment",
        "PCE", "IPP", "PMI", "Confiança", "Discurso",
        "Michigan", "Produtividade", "Custo Unitário", "Importados", "Importação"
    ]

    nome_evento = nome_evento.lower()

    for palavra in palavras_chave:
        if palavra.lower() in nome_evento:
            return True

    return False

async def enviar_eventos():
    try:
        agora = dt.datetime.now(TZ)
        hoje_str = agora.strftime("%Y-%m-%d")

        eventos_hoje = [e for e in EVENTOS_FIXOS if e["data"] == hoje_str]

        logging.info(f"[SCAN] {agora.strftime('%H:%M:%S')} | Eventos hoje: {len(eventos_hoje)}")

        eventos_agrupados = {}

        for evento in eventos_hoje:
            data_evento = dt.datetime.strptime(
                f"{evento['data']} {evento['hora']}",
                "%Y-%m-%d %H:%M"
            ).replace(tzinfo=TZ)

            diferenca = (data_evento - agora).total_seconds()
            impacto = EXPLICACOES.get(evento["nome"], {}).get("impacto", "MÉDIO")
            chave_id = f"{evento['data']}_{evento['hora']}_{evento['nome']}"

            logging.info(f"  {evento['hora']} | diff={int(diferenca)}s | {evento['nome'][:40]}")

            # ================= ALERTA 30 MIN =================
            if 0 < diferenca <= 1800 and chave_id not in alertados_30:
                await bot.send_message(
                    GROUP_ID,
                    f"⏳ FALTAM 30 MIN\n\n📊 {evento['nome']}\n🕒 {evento['hora']}"
                )
                alertados_30.add(chave_id)
                await asyncio.sleep(1)

            # ================= ALERTA 5 MIN (O MAIS CRÍTICO) =================
            if 0 < diferenca <= 300 and chave_id not in alertados_5:
                for i in range(5):
                    try:
                        await bot.send_message(
                            GROUP_ID,
                            "🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨\n"
                            "    EVENTO EM 5 MIN\n"
                            "🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨\n\n"
                            f"📊 {evento['nome']}\n"
                            f"🕒 {evento['hora']}\n\n"
                            "⚠️ EVITE ENTRADAS AGORA ⚠️"
                        )
                        await asyncio.sleep(1.2)
                    except Exception as e:
                        logging.error(f"Erro ao enviar alerta de 5min: {e}")
                        break
                alertados_5.add(chave_id)

            # ================= DIA PERIGOSO =================
            if 0 < diferenca <= 900 and (
                "ALTO" in impacto or
                "EXTREMO" in impacto or
                "MÁXIMO" in impacto
            ):
                eventos_agrupados.setdefault(evento["hora"], []).append(evento)

        # Verificação de dia perigoso
        for hora, lista in eventos_agrupados.items():
            if len(lista) >= 2 and hora not in alerta_dia_perigoso:

                alerta_dia_perigoso.add(hora)

                texto = (
                    f"🚨 DIA PERIGOSO (D)\n\n"
                    f"2 ou mais notícias fortes às {hora}\n\n"
                    f"{SEPARADOR}\n"
                    f"{assinatura_dj()}"
                )

                await bot.send_message(GROUP_ID, texto)

        # ================= JANELA DE VOLATILIDADE =================
        for evento in EVENTOS_FIXOS:

            if not relevante_para_nasdaq_ouro(evento["nome"]):
                continue

            data_evento = dt.datetime.strptime(
                f"{evento['data']} {evento['hora']}",
                "%Y-%m-%d %H:%M"
            ).replace(tzinfo=TZ)

            chave = f"janela_{evento['data']}_{evento['hora']}"
            diferenca = (data_evento - agora).total_seconds()
            impacto = EXPLICACOES.get(evento["nome"], {}).get("impacto", "MÉDIO")

            if 0 < diferenca <= 900 and chave not in alerta_janela:

                if any(x in impacto for x in ["ALTO", "EXTREMO", "MÁXIMO"]):

                    alerta_janela.add(chave)

                    texto = (
                        f"🌪 JANELA DE VOLATILIDADE\n\n"
                        f"Evento forte às {evento['hora']}.\n\n"
                        f"⚠️ Recomendações:\n"
                        f"• Evitar operar agora\n"
                        f"• Aguardar 15 minutos após o evento\n"
                        f"• Retornar somente se o mercado estabilizar\n\n"
                        f"{SEPARADOR}\n"
                        f"{assinatura_dj()}"
                    )

                    await bot.send_message(GROUP_ID, texto)

    except Exception as e:
        logging.error(f"[ERRO enviar_eventos] {e}", exc_info=True)

# ================= RESUMO SEMANAL =================

def formatar_data(data):
    if isinstance(data, str):
        data = dt.datetime.strptime(data, "%Y-%m-%d")
    return data.strftime("%d/%m/%Y")


def assinatura_dj():
    return "🎧 EconoBeat — UM DJ NA BOLSA"


def bolinha_importancia(nome_evento):
    impacto = EXPLICACOES.get(nome_evento, {}).get("impacto", "🟡 MÉDIO")

    if "MÁXIMO" in impacto:
        return "🔥"
    elif "EXTREMO" in impacto:
        return "🔴"
    elif "ALTO" in impacto:
        return "🟠"
    else:
        return "🟡"

async def resumo_semana_horario():
    global ultimo_relatorio_semana

    agora = dt.datetime.now(TZ)
    hora_atual = agora.hour

    if ultimo_relatorio_semana == hora_atual:
        return

    futuros = []

    for e in EVENTOS_FIXOS:
        if not relevante_para_nasdaq_ouro(e["nome"]):
            continue

        evento_dt = dt.datetime.strptime(
            f"{e['data']} {e['hora']}",
            "%Y-%m-%d %H:%M"
        ).replace(tzinfo=TZ)

        if agora <= evento_dt <= agora + dt.timedelta(days=7):
            futuros.append(e)

    if not futuros:
        return

    ultimo_relatorio_semana = hora_atual
    eventos_por_dia = {}

    for e in futuros:
        eventos_por_dia.setdefault(e["data"], []).append(e)

    texto = "📅 PRÓXIMOS EVENTOS DA SEMANA\n\n"

    for data in sorted(eventos_por_dia.keys()):
        data_dt = dt.datetime.strptime(data, "%Y-%m-%d")
        nome_dia = DIAS_SEMANA[data_dt.weekday()]
        dia_formatado = f"📌 {nome_dia} - {formatar_data(data)} 📌"

        texto += f"{SEPARADOR}\n{dia_formatado}\n{SEPARADOR}\n"

        for e in sorted(eventos_por_dia[data], key=lambda x: x["hora"]):
            bola = bolinha_importancia(e["nome"])
            texto += f"{bola} {e['hora']} — {e['nome']}\n"

        texto += "\n"

    texto += (
        f"{SEPARADOR}\n"
        "🔴 Extremo impacto\n"
        "🟠 Alto impacto\n"
        "🟡 Médio impacto\n\n"
        f"{assinatura_dj()}"
    )

    await bot.send_message(
        GROUP_ID,
        texto,
        parse_mode="Markdown"
    )

# ================= STATUS CMD =================
async def status_cmd():
    global ultimo_status_cmd
    agora = dt.datetime.now(TZ)

    if ultimo_status_cmd is None or (agora - ultimo_status_cmd).seconds >= 300:
        print(f"[STATUS] Sistema ativo | {agora.strftime('%H:%M:%S')}")
        ultimo_status_cmd = agora


# ================= ENCERRAMENTO DO DIA =================
async def encerramento_dia():
    global encerramento_enviado

    agora = dt.datetime.now(TZ)
    chave = agora.strftime("%Y-%m-%d")

    # ✅ ENCERRAMENTO FIXO 18:00
    if agora.hour == 18 and agora.minute == 0:

        if chave not in encerramento_enviado:
            encerramento_enviado.add(chave)

            texto = (
                f"⏰ ENCERRAMENTO DO DIA\n\n"
                "O pregão do Nasdaq & Ouro chegou ao fim.\n"
                "Revise suas operações, registre insights e prepare o plano para amanhã.\n\n"
                f"{SEPARADOR}\n"
                f"{assinatura_dj()}"
            )

            await bot.send_message(
                GROUP_ID,
                texto,
                parse_mode="Markdown"
            )


# ================= MAIN =================
async def main():
    scheduler = AsyncIOScheduler(timezone=TZ)

    scheduler.add_job(enviar_eventos, "interval", seconds=30)
    scheduler.add_job(resumo_semana_horario, "interval", minutes=1)
    scheduler.add_job(encerramento_dia, "interval", minutes=1)
    scheduler.add_job(status_cmd, "interval", minutes=1)

    scheduler.start()

    print("Bot iniciado (Nasdaq & Ouro)")

    await resumo_semana_horario()

    while True:
        await asyncio.sleep(60)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())