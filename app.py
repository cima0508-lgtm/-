import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# --- ページ設定 ---
st.set_page_config(
    page_title="芦北の「たんぼ」",                # タブのタイトル
    page_icon="ine_icon_1024.png",             # 画像ファイルを指定
    layout="wide",                             # "centered" から "wide" に変更して崩れを確認
    initial_sidebar_state="collapsed"          # スマホ表示のためにサイドバーを閉じておく
)

# --- カスタムCSSで再調整（サイドバーボタンを救出） ---
st.markdown("""
    <style>
        /* 1. 最上部の文字が消えないよう、上の余白を少し広めに確保 (2.5rem) */
        .block-container {
            padding-top: 2.5rem !important;
        }

        /* 2. 要素間の隙間(gap)を完全にゼロにする */
        [data-testid="stVerticalBlock"] {
            gap: 0rem !important;
        }
        
        /* 3. 各パーツ(圃場名、日付、表)の上下の余白を最小化 */
        [data-testid="stVerticalBlock"] > div {
            margin-top: 0rem !important;
            margin-bottom: 0.2rem !important;
            padding-top: 0rem !important;
            padding-bottom: 0rem !important;
        }

        /* 4. サイドバーボタンをタイトルの邪魔にならない位置へ */
        button[kind="header"] {
            top: 1.0rem !important;
        }
    </style>
""", unsafe_allow_html=True)

# ブラウザの自動翻訳を防ぐための設定
st.markdown('<meta name="google" content="notranslate">', unsafe_allow_html=True)
st.markdown('<html lang="ja">', unsafe_allow_html=True)

# --- タイトルとサブタイトルの表示 ---
# 念のため、タイトル自体の上のマージンも0に指定しておきます
st.markdown("<h2 style='text-align: center; font-size: 24px; margin-top: 0;'>🌾 水稲生育・収穫システム</h2>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; font-size: 18px; color: #555; margin-top: -10px;'>芦北の「たんぼ」</h3>", unsafe_allow_html=True)


# --- データの読み込み関数 ---
@st.cache_data
def load_master_data():
    return pd.read_excel("data.xlsx", sheet_name='data')

def load_temp_data(filename):
    try:
        df = pd.read_csv(filename)
        return dict(zip(df['年月日'].astype(str), df['平均気温(℃)']))
    except:
        return {}

# --- 計算ロジック ---
def predict_harvest(heading_date, target_temp, current_temps, last_temps, correction):
    accumulated_temp = 0
    check_date = heading_date.date() if isinstance(heading_date, datetime) else heading_date

    for _ in range(1, 101):
        ts_check = str(check_date)
        temp = current_temps.get(ts_check)
        if temp is None:
            try:
                last_year_date = str(check_date.replace(year=check_date.year - 1))
                temp = last_temps.get(last_year_date, 25.0)
            except:
                temp = 25.0

        field_temp = temp - correction
        accumulated_temp += field_temp
        if accumulated_temp >= target_temp:
            return check_date, accumulated_temp, True
        check_date += timedelta(days=1)
    return None, 0, False

# ==============================================================================
# 💡 ここに移動してください（カレンダーを使う関数は先に定義）
# ==============================================================================
def color_rows(row):
    if "出穂(基準)" in str(row['作業項目']): return ['color: #FF0000; font-weight: bold;'] * len(row)
    if "収穫適期" in str(row['作業項目']): return ['color: #008000; font-weight: bold;'] * len(row)
    if not row['確定']: return ['color: #A0A0A0; font-weight: normal;'] * len(row)
    return ['color: #000000; font-weight: bold;'] * len(row)
# ==============================================================================

# --- メイン処理 ---
df = load_master_data()

# --- サイドバー：選択メニュー ---
st.sidebar.header("📋 選択メニュー")
hinsyu_list = df['品種名'].unique().tolist()
selected_hinsyu = st.sidebar.selectbox("1. 品種を選択", hinsyu_list)
available_hojo = df[df['品種名'] == selected_hinsyu]['圃場名'].tolist()
selected_hojo = st.sidebar.selectbox("2. 圃場を選択", available_hojo)
selected_name = f"{selected_hinsyu}（{selected_hojo}）"

match_row = df[(df['品種名'] == selected_hinsyu) & (df['圃場名'] == selected_hojo)]
if match_row.empty:
    st.error("該当するデータが見つかりません。")
    st.stop()
row = match_row.iloc[0]

# --- セッション状態の初期化 ---
if 'show_water' not in st.session_state:
    st.session_state.show_water = False
if 'planting_dates' not in st.session_state:
    st.session_state.planting_dates = {}
if selected_name not in st.session_state.planting_dates:
    st.session_state.planting_dates[selected_name] = datetime.now().date()

# ==============================================================================
# 🛠️ 入力項目修正：年を自動取得し、レイアウトを縦並びにして携帯対応
# 🛠️ 入力項目修正：出穂日実績のデフォルトを「未入力」にする
# ==============================================================================

# 今日の日付を取得
today = datetime.now().date()
current_planting_date = st.session_state.planting_dates[selected_name]

# 動的に西暦リストを作成 (前年と今年)
year_list = [today.year - 1, today.year]

st.sidebar.markdown("### 📅 日付設定")

# 1. 田植え日の設定
st.sidebar.markdown("#### ① 田植え日")
p_year = st.sidebar.selectbox("年", options=year_list, index=1 if current_planting_date.year == today.year else 0, key="p_year_s")
p_month = st.sidebar.selectbox("月", options=[5, 6, 7], index=[5, 6, 7].index(current_planting_date.month) if current_planting_date.month in [5, 6, 7] else 0, key="p_month_s")
p_day = st.sidebar.selectbox("日", options=list(range(1, 32)), index=current_planting_date.day - 1, key="p_day_s")

try:
    planting_date = datetime(p_year, p_month, p_day).date()
    st.session_state.planting_dates[selected_name] = planting_date
except ValueError:
    st.sidebar.error("無効な日付です")
    planting_date = current_planting_date

# 2. 出穂日の設定 (未入力・実績に対応)
st.sidebar.markdown("#### ② 出穂日実績 (任意)")

# 実績入力の有効化フラグを追加
use_actual_heading = st.sidebar.checkbox("実績を入力する", key="use_actual")

if use_actual_heading:
    # チェックを入れたときだけ表示される
    h_year = st.sidebar.selectbox("年", options=year_list, index=1, key="h_year_s")
    h_month = st.sidebar.selectbox("月", options=[5, 6, 7, 8, 9, 10], index=2, key="h_month_s")
    h_day = st.sidebar.selectbox("日", options=list(range(1, 32)), index=0, key="h_day_s")

    try:
        actual_heading_date = datetime(h_year, h_month, h_day).date()
    except ValueError:
        actual_heading_date = None
else:
    # チェックがないときはNoneにする
    actual_heading_date = None

# ==============================================================================
# --- 気温データの読み込み ---
current_year = planting_date.year
current_temps = load_temp_data(f"{current_year}data.csv")
last_temps = load_temp_data(f"{current_year-1}data.csv")

# --- 出穂・収穫計算 ---
if actual_heading_date:
    base_heading_date = actual_heading_date
    status_msg = "✅ 出穂実績に基づき計算"
    # 表示用の日付ラベルを作成
    date_label = f"📅 出穂実績日: {actual_heading_date.strftime('%Y/%m/%d')}"
else:
    base_heading_date = planting_date + timedelta(days=int(row["出穂までの日数"]))
    status_msg = "💡 予測出穂日に基づき計算"
    # 表示用の日付ラベルを作成
    date_label = f"📅 設定田植日: {planting_date.strftime('%Y/%m/%d')}"

# ==========================================
# 🚀 画面表示ここから
# ==========================================

# 1. 📍 圃場情報（日付情報を追加して表示）
st.info(f"📍 **{row['圃場名']}**　({date_label})\n\n{status_msg}")

correction = (row["圃場標高"] - row["アメダス標高"]) / 100 * 0.6
harvest_date, total_temp, is_forecast = predict_harvest(base_heading_date, row["目標積算温度（収穫）"], current_temps, last_temps, correction)


# 2. 💧 水管理・防除パネル（ボタン判定をここに直結）
st.sidebar.markdown("---")
# サイドバーのボタンが押されたら、即座に状態をTrueにする
if st.sidebar.button("💧 水管理・防除を確認"):
    st.session_state.show_water = True

# 「表示フラグ」がTrueの時だけ、カレンダーの上に表示する
if st.session_state.show_water:

    # ▼ タイトルサイズをF3相当に変更（中央寄せ）
    st.markdown(
        """
        <div style="
            text-align:center;
            font-size:18px;
            font-weight:600;
            margin-bottom:10px;
        ">
        💧 生育ステージ別 水管理・防除
        </div>
        """,
        unsafe_allow_html=True
    )

    html_content = """
    <div style="font-family: sans-serif; background-color: #f9f9f9; padding: 8px; border-radius: 8px;">
        <style>
            .row { display: flex; align-items: center; margin-bottom: 8px; width: 100%; }
            .label { width: 90px; padding: 6px 2px; text-align: center; border-radius: 4px; font-weight: bold; font-size: 11px; color: black; border: 1px solid #ddd; flex-shrink: 0; }
            .day { width: 32px; height: 32px; background: #4472C4; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 8px; font-weight: bold; font-size: 11px; flex-shrink: 0; }
            .stage { flex: 1; padding: 6px; border-radius: 4px; border: 1px solid #ccc; background: #C6EFCE; color: black; font-size: 13px; line-height: 1.2; }
            .prevent { font-size: 10px; margin-top: 3px; padding: 3px; background: white; border: 2px solid #d9534f; color: #d9534f; font-weight: bold; border-radius: 3px; }
        </style>
        <div class="row"><div class="label" style="background:#CCFFFF;">深水 5cm</div><div class="day">-80</div><div class="stage">活着期</div></div>
        <div class="row"><div class="label" style="background:#CCFFFF;">浅水 3cm</div><div class="day">-70</div><div class="stage">有効分けつ期</div></div>
        <div class="row"><div class="label" style="background:#70AD47; color:white;">中干し</div><div class="day">-40</div><div class="stage">無効分けつ期</div></div>
        <div class="row"><div class="label" style="background:#CCFFFF;">間断灌水</div><div class="day">-20</div><div class="stage">幼穂形成期<div class="prevent">⚠️ 紋枯、ウンカ、コブノメイガ</div></div></div>
        <div class="row"><div class="label" style="background:#CCFFFF;">灌水</div><div class="day">0</div><div class="stage">出穂期 (5割)<div class="prevent">⚠️ いもち、紋枯、ウンカ</div></div></div>
        <div class="row"><div class="label" style="background:#F8CBAD;">落水</div><div class="day">40</div><div class="stage" style="background:#F8CBAD;">収穫期</div></div>
    </div>
    """
    st.components.v1.html(html_content, height=380, scrolling=True)

    # 閉じるボタン
    if st.button("❌ 管理画面を閉じる"):
        st.session_state.show_water = False
        st.rerun()

    st.markdown("---")

# --- 3. 📅 工程カレンダー ---
st.write("### 📅 工程カレンダー")

# 【1】まず最初にデータを定義する（これで NameError を防ぎます）
today_val = datetime.now().date()
data_list = [
    {"作業項目": "🚜 中干し開始目安", "予定日": (planting_date + timedelta(days=40))},
    {"作業項目": "💎 穂肥１", "予定日": (base_heading_date - timedelta(days=25))},
    {"作業項目": "🌿 幼穂形成期", "予定日": (base_heading_date - timedelta(days=20))},
    {"作業項目": "💎 穂肥２", "予定日": (base_heading_date - timedelta(days=10))},
    {"作業項目": "🌾 穂ばらみ期", "予定日": (base_heading_date - timedelta(days=7))},
    {"作業項目": "🚩 出穂(基準)", "予定日": base_heading_date},
    {"作業項目": "💧 乳熟期", "予定日": (base_heading_date + timedelta(days=10))},
    {"作業項目": "☁️ 登熟期", "予定日": (base_heading_date + timedelta(days=20))},
    {"作業項目": "🚿 落水期", "予定日": (base_heading_date + timedelta(days=30))},
    {"作業項目": "🌾 収穫適期(予測)", "予定日": harvest_date if harvest_date else "計算中..."},
]

# 【2】データフレームを作成
df_display = pd.DataFrame(data_list)

# 【3】色塗りと日付フォーマットを一括適用
# .style.apply で色を決め、.format で見た目を 05/20 にします
try:
    styled_df = df_display.style.apply(color_rows, axis=1).format({
        "予定日": lambda x: x.strftime('%m/%d') if hasattr(x, 'strftime') else str(x)
    })
    # 表示
    st.table(styled_df)
except Exception as e:
    # 万が一エラーが出た場合は普通の表を表示（全消え防止）
    st.table(df_display)

# 【4】注釈を表示
st.markdown(
    f"""
    <div style="font-size: 11px; color: gray; line-height: 1.2; margin-top: 5px;">
        ※中干し:茎数20-25本で開始 / ※草刈:出穂14日前までに完了<br>
        （※標高補正: {correction:.2f}℃ 減算）
    </div>
    """,
    unsafe_allow_html=True
)

# --- 以下、説明書などのコードが続く ---

# --- 説明書 ---
st.write("---")
st.download_button(label="📄 説明書をダウンロード", data="水稲栽培管理シミュレーター 説明書", file_name="readme.txt")
