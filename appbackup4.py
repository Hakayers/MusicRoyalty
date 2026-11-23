import streamlit as st
import streamlit.components.v2 as components
import json
import re
import hashlib
import html as htmllib
from decimal import Decimal, InvalidOperation
from pathlib import Path
from datetime import datetime
from web3 import Web3

try:
    import plotly.graph_objects as go
    PLOTLY = True
except Exception:  # plotly opsional, ada fallback
    PLOTLY = False


# Kompatibilitas versi Streamlit: width="stretch" hanya ada di versi baru
def _st_version():
    try:
        return tuple(int(x) for x in st.__version__.split(".")[:2])
    except Exception:
        return (0, 0)

STRETCH = {"width": "stretch"} if _st_version() >= (1, 50) else {"use_container_width": True}

# =========================================================
# 1. KONFIGURASI
# =========================================================

RPC_URL = "http://127.0.0.1:8545"
DEPLOYMENT_PATH = Path(__file__).parent / "deployment.json"

CONTRACT_ADDRESS = None
if DEPLOYMENT_PATH.exists():
    with open(DEPLOYMENT_PATH, "r") as f:
        CONTRACT_ADDRESS = json.load(f).get("contractAddress")

ABI_PATH = (
    Path(__file__).parent / "artifacts" / "contracts"
    / "MusicRoyalty.sol" / "MusicRoyalty.json"
)

# Pembagian royalti sesuai smart contract
PARTICIPANTS = [
    ("Kreator", 60, "#7c3aed"),
    ("Produser", 20, "#db2777"),
    ("Penulis Lagu", 15, "#f97316"),
    ("Platform Musik", 5, "#0ea5e9"),
]

STATUS_COLORS = {
    "CREATED": ("#2563eb", "rgba(37,99,235,.14)"),
    "USED": ("#d97706", "rgba(217,119,6,.14)"),
    "DISTRIBUTED": ("#7c3aed", "rgba(124,58,237,.14)"),
    "COMPLETED": ("#16a34a", "rgba(22,163,74,.14)"),
}

USAGE_TYPES = ["Streaming", "Download", "Radio", "Live Performance", "Sync License", "Lainnya"]

PAGES = [
    "🏠 Dashboard",
    "📚 Music Catalog",
    "📝 Register Music",
    "🔎 Music Detail",
    "💰 Royalty Distribution",
    "📜 Royalty History",
    "👛 Wallet & Transaction",
]

st.set_page_config(
    page_title="MusicRoyalty Dashboard",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================================================
# 2. STYLE
# =========================================================

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700;9..144,800&family=DM+Sans:wght@400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

:root {
    --cream: #faf6ef; --paper: #ffffff; --sand: #f1eadb; --ink: #1c1917; --muted: #6b6258;
    --line: #e7dfd0; --accent: #e4572e; --accent-d: #c2411c; --green: #1f6f5c; --amber: #f2a900;
}
html, body, [class*="css"], .stMarkdown, button, input, textarea, select {
    font-family: 'DM Sans', sans-serif !important;
}
code, pre, .stCode * { font-family: 'DM Mono', monospace !important; }
h1, h2, h3, .hero h1, .stat-value, .mc-title, .side-brand, .section-title {
    font-family: 'Fraunces', serif !important;
}

.stApp { background: var(--cream); background-image: radial-gradient(rgba(28,25,23,.05) 1px, transparent 1px); background-size: 22px 22px; }
.block-container { padding-top: 1.6rem; max-width: 1200px; }
header[data-testid="stHeader"] { background: transparent; }
.stCaption, [data-testid="stCaptionContainer"] { color: var(--muted) !important; }

/* Paksa warna teks agar terbaca di tema Streamlit gelap maupun terang */
.stApp p, .stApp li, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp label,
.stApp [data-testid="stMarkdownContainer"], .stApp [data-testid="stWidgetLabel"] *,
.stApp [data-testid="stMetricLabel"] *, .stApp [data-testid="stMetricValue"] *,
.stApp [data-testid="stRadio"] label *, .stApp [data-testid="stCheckbox"] label * { color: var(--ink); }
.stApp input, .stApp textarea { color: #fff !important; -webkit-text-fill-color: #fff !important; }
.stApp input::placeholder, .stApp textarea::placeholder { color: rgba(255,255,255,.6) !important; -webkit-text-fill-color: rgba(255,255,255,.6) !important; opacity: 1; }
.stApp div[data-baseweb="select"] * { color: #fff !important; }
.stApp pre, .stApp pre *, .stApp [data-testid="stCode"] * { background: var(--sand) !important; color: var(--ink) !important; }
.stApp button[kind="primary"] p, .stApp button[kind="primaryFormSubmit"] p { color: #fff !important; }
div[data-testid="stAlert"] { background: var(--paper) !important; }
div[data-testid="stAlert"] * { color: var(--ink) !important; }

@keyframes spin { to { transform: rotate(360deg); } }
@keyframes floatIn { from {opacity: 0; transform: translateY(10px);} to {opacity: 1; transform: translateY(0);} }
@keyframes pulse { 0% {box-shadow: 0 0 0 0 currentColor;} 70% {box-shadow: 0 0 0 6px transparent;} 100% {box-shadow: 0 0 0 0 transparent;} }
[data-stale="true"], .stale-element, div[data-testid="stAppViewBlockContainer"] * { transition: none; }
[data-stale="true"] { opacity: 1 !important; }
.stApp, .stApp > header { transition: none !important; }

/* HERO */
.hero {
    position: relative; overflow: hidden; background: var(--ink); color: var(--cream);
    border-radius: 24px; padding: 2.1rem 2.4rem; margin-bottom: 1.6rem; display: flex; align-items: center; gap: 1.6rem;
    box-shadow: 8px 8px 0 var(--accent);
}
.hero-icon { font-size: 2rem; width: 66px; height: 66px; min-width: 66px; border-radius: 18px; background: var(--accent);
    display: flex; align-items: center; justify-content: center; }
.hero h1 { margin: 0; padding: 0; font-size: 2.1rem; color: var(--cream) !important; font-weight: 700; letter-spacing: -.01em; }
.hero p { margin: .35rem 0 0; color: rgba(250,246,239,.75) !important; font-size: .98rem; max-width: 560px; }
.vinyl {
    position: absolute; right: -50px; top: 50%; margin-top: -120px; width: 240px; height: 240px; border-radius: 50%;
    background:
        radial-gradient(circle, var(--accent) 0 17%, #111 17.5% 19%, transparent 19.5%),
        repeating-radial-gradient(circle, #1a1715 0 3px, #2a2522 3px 4px);
    border: 2px solid #3a332e; animation: spin 9s linear infinite; opacity: .95;
}
.vinyl::after { content: ""; position: absolute; inset: 0; border-radius: 50%;
    background: conic-gradient(from 30deg, transparent 0 20%, rgba(255,255,255,.12) 25%, transparent 30% 70%, rgba(255,255,255,.1) 75%, transparent 80%); }

/* STAT CARD */
.stat-card {
    background: var(--paper); border: 1.5px solid var(--ink); border-radius: 18px; padding: 1.1rem 1.25rem; height: 100%;
    box-shadow: 4px 4px 0 var(--ink); transition: transform .15s ease, box-shadow .15s ease;
}
.stat-card:hover { transform: translate(-2px,-2px); box-shadow: 7px 7px 0 var(--accent); }
.stat-top { display: flex; justify-content: space-between; align-items: center; }
.stat-label { font-size: .7rem; color: var(--muted) !important; font-weight: 700; text-transform: uppercase; letter-spacing: .1em; }
.stat-icon { font-size: 1.1rem; width: 36px; height: 36px; display: flex; align-items: center; justify-content: center; background: var(--sand); border-radius: 50%; }
.stat-value { font-size: 2rem; font-weight: 700; margin-top: .5rem; line-height: 1.1; overflow-wrap: anywhere; color: var(--ink); }
.stat-sub { font-size: .8rem; color: var(--muted) !important; margin-top: .25rem; }

/* PILL & BADGE */
.pill { display: inline-flex; align-items: center; gap: .5rem; padding: .38rem .85rem; border-radius: 999px; font-size: .78rem; font-weight: 700; margin: 0 .5rem .5rem 0; border: 1.5px solid; }
.pill-ok { background: #dcfce7; color: #166534 !important; border-color: #86efac; }
.pill-bad { background: #fee2e2; color: #991b1b !important; border-color: #fca5a5; }
.pill-warn { background: #fef3c7; color: #92400e !important; border-color: #fcd34d; }
.dot { width: 8px; height: 8px; border-radius: 50%; background: currentColor; display: inline-block; animation: pulse 2s infinite; }
.badge { display: inline-block; padding: .22rem .7rem; border-radius: 8px; font-size: .7rem; font-weight: 800; letter-spacing: .08em; border: 1.5px solid currentColor; }

/* MUSIC CARD */
.music-card {
    position: relative; background: var(--paper); border: 1.5px solid var(--ink); border-radius: 18px;
    padding: 1.2rem 1.3rem 1.1rem; margin-bottom: .6rem; overflow: hidden; box-shadow: 4px 4px 0 var(--ink); transition: all .15s ease;
}
.music-card::after { content: ""; position: absolute; right: -26px; top: -26px; width: 90px; height: 90px; border-radius: 50%;
    background: repeating-radial-gradient(circle, var(--sand) 0 3px, var(--paper) 3px 6px); opacity: .9; }
.music-card:hover { transform: translate(-2px,-2px); box-shadow: 7px 7px 0 var(--accent); }
.music-card .mc-id { font-size: .7rem; color: var(--accent-d) !important; font-weight: 800; letter-spacing: .1em; text-transform: uppercase; }
.music-card .mc-title { font-size: 1.25rem; font-weight: 700; margin: .25rem 0 .6rem; overflow-wrap: anywhere; color: var(--ink); position: relative; z-index: 1; }
.music-card .mc-row { font-size: .86rem; color: var(--muted) !important; margin-top: .3rem; overflow-wrap: anywhere; }

/* INFO CARD */
.info-card { background: var(--paper); border: 1.5px solid var(--ink); border-radius: 18px; padding: 1.1rem 1.5rem; box-shadow: 4px 4px 0 var(--ink); }
.info-row { display: flex; justify-content: space-between; align-items: center; gap: 1rem; padding: .7rem 0; border-bottom: 1.5px dotted var(--line); }
.info-row:last-child { border-bottom: none; }
.info-key { color: var(--muted) !important; font-size: .85rem; font-weight: 600; }
.info-val { font-weight: 700; text-align: right; overflow-wrap: anywhere; color: var(--ink); }
.info-val code { background: var(--sand); color: var(--ink); padding: .15rem .5rem; border-radius: 6px; font-size: .76rem; }

/* TIMELINE */
.timeline { border-left: 2px dashed var(--ink); margin-left: .7rem; padding-left: 1.5rem; }
.tl-item { position: relative; margin-bottom: 1rem; background: var(--paper); border: 1.5px solid var(--line); border-radius: 14px; padding: .8rem 1rem; }
.tl-item::before { content: ""; position: absolute; left: -2.02rem; top: 1rem; width: 14px; height: 14px; border-radius: 50%;
    background: var(--accent); border: 3px solid var(--cream); box-shadow: 0 0 0 2px var(--ink); }
.tl-title { font-weight: 700; color: var(--ink); }
.tl-meta { font-size: .8rem; color: var(--muted) !important; overflow-wrap: anywhere; margin-top: .2rem; }

.section-title { font-size: 1.25rem; font-weight: 700; margin: 1.4rem 0 .7rem; display: flex; align-items: center; gap: .7rem; color: var(--ink); }
.section-title::after { content: ""; flex: 1; height: 2px; background: var(--ink); opacity: .12; }

/* SIDEBAR */
section[data-testid="stSidebar"] { background: var(--sand); border-right: 2px solid var(--ink); }
.side-brand { font-size: 1.5rem; font-weight: 800; color: var(--ink); letter-spacing: -.01em; }
.side-sub { font-size: .74rem; color: var(--muted) !important; margin-bottom: 1.1rem; }
section[data-testid="stSidebar"] div[role="radiogroup"] { gap: .35rem; }
section[data-testid="stSidebar"] div[role="radiogroup"] label {
    background: transparent; border: 1.5px solid transparent; border-radius: 12px; padding: .55rem .85rem; width: 100%; transition: all .12s ease; cursor: pointer;
}
section[data-testid="stSidebar"] div[role="radiogroup"] label:hover { background: rgba(255,255,255,.65); }
section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
    background: var(--ink); border-color: var(--ink); box-shadow: 3px 3px 0 var(--accent);
}
section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) p { color: var(--cream) !important; }
section[data-testid="stSidebar"] div[role="radiogroup"] label > div:first-child { display: none; }
section[data-testid="stSidebar"] div[role="radiogroup"] label p { font-weight: 700; font-size: .92rem; }

/* INPUTS */
div[data-baseweb="input"], div[data-baseweb="select"] > div, div[data-baseweb="textarea"], .stNumberInput > div > div {
    background: var(--paper) !important; border: 1.5px solid var(--ink) !important; border-radius: 12px !important;
}
div[data-baseweb="input"]:focus-within, div[data-baseweb="select"] > div:focus-within {
    border-color: var(--accent) !important; box-shadow: 3px 3px 0 var(--accent) !important;
}
div[data-testid="stForm"] { background: var(--paper); border: 1.5px solid var(--ink); border-radius: 18px; padding: 1.3rem; box-shadow: 4px 4px 0 var(--ink); }
[data-testid="stFileUploader"] section { background: var(--paper); border: 2px dashed var(--ink); border-radius: 14px; }

/* BUTTONS */
div.stButton > button, div[data-testid="stFormSubmitButton"] > button, div.stDownloadButton > button {
    border-radius: 12px; font-weight: 700; padding: .55rem 1.2rem; border: 1.5px solid var(--ink); background: var(--paper); color: var(--ink);
    box-shadow: 3px 3px 0 var(--ink); transition: all .12s ease;
}
div.stButton > button:hover, div.stDownloadButton > button:hover { transform: translate(-1px,-1px); box-shadow: 5px 5px 0 var(--ink); border-color: var(--ink); color: var(--ink); }
div.stButton > button:active { transform: translate(2px,2px); box-shadow: 1px 1px 0 var(--ink); }
div[data-testid="stFormSubmitButton"] > button[kind="primary"], div.stButton > button[kind="primary"],
div[data-testid="stFormSubmitButton"] > button[kind="primaryFormSubmit"] {
    background: var(--accent) !important; color: #fff !important; border: 1.5px solid var(--ink) !important;
}
div.stButton > button[kind="primary"]:hover { background: var(--accent-d) !important; }

/* TABS, METRIC, ALERT, TABLE */
div[data-testid="stTabs"] [role="tablist"] { gap: .4rem; border-bottom: 2px solid var(--ink); }
div[data-testid="stTabs"] button[role="tab"] { font-weight: 700; border-radius: 10px 10px 0 0; padding: .55rem 1rem; }
div[data-testid="stTabs"] button[aria-selected="true"] { background: var(--ink); }
div[data-testid="stTabs"] button[aria-selected="true"] p { color: var(--cream) !important; }
div[data-testid="stMetric"] { background: var(--paper); border: 1.5px solid var(--ink); border-radius: 14px; padding: .9rem 1rem; }
div[data-testid="stMetricValue"] { font-weight: 700; font-family: 'Fraunces', serif !important; }
div[data-testid="stAlert"] { border-radius: 14px; border: 1.5px solid var(--ink); }
div[data-testid="stDataFrame"] { border-radius: 14px; overflow: hidden; border: 1.5px solid var(--ink); }
div[data-testid="stExpander"] { background: var(--paper); border: 1.5px solid var(--ink); border-radius: 14px; }
hr { border-color: var(--line) !important; }
::-webkit-scrollbar { width: 8px; height: 8px; } ::-webkit-scrollbar-thumb { background: var(--ink); border-radius: 8px; }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# =========================================================
# 3. KOMPONEN METAMASK (WALLET + TRANSAKSI GENERIK)
# =========================================================

WALLET_HTML = """
<div class="wb">
    <button id="connect-wallet" type="button">🦊 Connect MetaMask</button>
    <p id="wallet-status">Wallet belum terhubung.</p>
</div>
"""

WALLET_CSS = """
button {
    width: 100%; padding: 0.65rem 1rem; border: none; border-radius: 12px;
    background: linear-gradient(135deg, #f6851b, #e2761b); color: white;
    font-weight: 700; cursor: pointer; font-size: 0.9rem;
}
button:hover { filter: brightness(1.08); }
p { color: var(--st-text-color); overflow-wrap: anywhere; font-size: 0.8rem; opacity: .8; margin: .5rem 0 0; }
"""

WALLET_JS = """
export default function(component) {
    const { parentElement, setStateValue } = component;
    const button = parentElement.querySelector("#connect-wallet");
    const status = parentElement.querySelector("#wallet-status");
    let mounted = true;
    let last = "";
    function push(v) {
        const k = JSON.stringify(v);
        if (k === last) return;
        last = k;
        setStateValue("wallet", v);
    }

    async function readWallet() {
        if (!window.ethereum) return;
        const accounts = await window.ethereum.request({ method: "eth_accounts" });
        const chainId = await window.ethereum.request({ method: "eth_chainId" });
        if (!mounted) return;
        const connected = accounts && accounts.length > 0;
        push({
            address: connected ? accounts[0] : "",
            chainId: chainId,
            connected: connected
        });
        status.textContent = connected
            ? "Terhubung: " + accounts[0].slice(0, 8) + "..." + accounts[0].slice(-6)
            : "Wallet belum terhubung.";
        button.textContent = connected ? "🦊 Wallet Terhubung" : "🦊 Connect MetaMask";
    }

    async function connectWallet() {
        if (!window.ethereum) {
            status.textContent = "MetaMask tidak ditemukan.";
            return;
        }
        try {
            status.textContent = "Menunggu persetujuan MetaMask...";
            await window.ethereum.request({ method: "eth_requestAccounts" });
            await readWallet();
        } catch (error) {
            status.textContent = "Koneksi gagal: " + error.message;
        }
    }

    function onAccountsChanged(accounts) {
        if (!mounted) return;
        window.ethereum.request({ method: "eth_chainId" }).then((chainId) => {
            if (!mounted) return;
            push({
                address: accounts.length > 0 ? accounts[0] : "",
                chainId: chainId,
                connected: accounts.length > 0
            });
            readWallet().catch(() => {});
        }).catch(() => {});
    }

    function onChainChanged(chainId) {
        if (!mounted) return;
        window.ethereum.request({ method: "eth_accounts" }).then((accounts) => {
            if (!mounted) return;
            push({
                address: accounts.length > 0 ? accounts[0] : "",
                chainId: chainId,
                connected: accounts.length > 0
            });
        }).catch(() => {});
    }

    button.addEventListener("click", connectWallet);

    if (window.ethereum) {
        window.ethereum.on("accountsChanged", onAccountsChanged);
        window.ethereum.on("chainChanged", onChainChanged);
        readWallet().catch(() => {});
    }

    return () => {
        mounted = false;
        button.removeEventListener("click", connectWallet);
        if (window.ethereum && window.ethereum.removeListener) {
            window.ethereum.removeListener("accountsChanged", onAccountsChanged);
            window.ethereum.removeListener("chainChanged", onChainChanged);
        }
    };
}
"""

wallet_component = components.component(
    name="musicroyalty_wallet",
    html=WALLET_HTML,
    css=WALLET_CSS,
    js=WALLET_JS,
)

TX_HTML = """
<div>
    <button id="tx-btn" type="button" disabled>Menunggu data transaksi...</button>
    <p id="tx-status">Isi form terlebih dahulu.</p>
</div>
"""

TX_CSS = """
button {
    padding: 0.75rem 1.2rem; border: none; border-radius: 12px;
    background: linear-gradient(135deg, #7c3aed, #db2777);
    color: white; font-weight: 700; cursor: pointer; font-size: 0.95rem;
}
button:hover:not(:disabled) { filter: brightness(1.1); }
button:disabled { opacity: 0.45; cursor: not-allowed; }
p { color: var(--st-text-color); overflow-wrap: anywhere; font-size: 0.85rem; opacity: .85; }
"""

TX_JS = """
export default function(component) {
    const { parentElement, data, setTriggerValue } = component;
    const button = parentElement.querySelector("#tx-btn");
    const status = parentElement.querySelector("#tx-status");
    let mounted = true;

    const tx = data && data.transaction ? data.transaction : null;
    const label = data && data.label ? data.label : "Konfirmasi melalui MetaMask";
    const idle = data && data.idle ? data.idle : "Isi form terlebih dahulu.";

    if (tx && tx.to && tx.data && tx.from) {
        button.disabled = false;
        button.textContent = "🦊 " + label;
        status.textContent = "Transaksi siap dikirim. Periksa akun dan detail transaksi di MetaMask.";
    } else {
        button.disabled = true;
        button.textContent = "Menunggu data transaksi...";
        status.textContent = idle;
    }

    async function sendTransaction() {
        if (!tx) return;
        if (!window.ethereum) {
            status.textContent = "MetaMask tidak ditemukan.";
            setTriggerValue("tx_error", { message: "MetaMask tidak ditemukan." });
            return;
        }
        button.disabled = true;
        status.textContent = "Memeriksa akun dan jaringan MetaMask...";
        try {
            const accounts = await window.ethereum.request({ method: "eth_requestAccounts" });
            const chainId = await window.ethereum.request({ method: "eth_chainId" });

            if (!accounts || accounts.length === 0) {
                throw new Error("Hubungkan akun MetaMask terlebih dahulu.");
            }
            if (accounts[0].toLowerCase() !== tx.from.toLowerCase()) {
                throw new Error("Akun MetaMask berubah. Pilih kembali akun yang terhubung di dashboard.");
            }
            if (parseInt(chainId, 16) !== Number(tx.chainId)) {
                throw new Error("Jaringan MetaMask tidak sesuai. Pilih Hardhat Local (Chain ID 31337).");
            }

            status.textContent = "⏳ Menunggu konfirmasi transaksi di MetaMask...";
            const params = { from: tx.from, to: tx.to, data: tx.data };
            if (tx.value) { params.value = tx.value; }

            const txHash = await window.ethereum.request({
                method: "eth_sendTransaction",
                params: [params]
            });

            status.textContent = "✅ Transaksi dikirim: " + txHash;
            if (mounted) {
                setTriggerValue("tx_submitted", { txHash: txHash, requestId: tx.requestId });
            }
        } catch (error) {
            status.textContent = "❌ Transaksi gagal: " + error.message;
            if (mounted) {
                setTriggerValue("tx_error", { message: error.message });
            }
            button.disabled = false;
        }
    }

    button.addEventListener("click", sendTransaction);
    return () => {
        mounted = false;
        button.removeEventListener("click", sendTransaction);
    };
}
"""

tx_component = components.component(
    name="musicroyalty_tx",
    html=TX_HTML,
    css=TX_CSS,
    js=TX_JS,
)


# =========================================================
# 4. SESSION STATE
# =========================================================

defaults = {
    "tx_log": [],
    "tx_results": {},
    "req_id": 0,
    "selected_batch": None,
    "nav": PAGES[0],
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v



# =========================================================
# 5. KONEKSI BLOCKCHAIN & SMART CONTRACT
# =========================================================

w3 = Web3(
    Web3.HTTPProvider(
        RPC_URL,
        request_kwargs={"timeout": 5}
    )
)


@st.cache_data(ttl=5, show_spinner=False)
def load_chain_state(rpc_url, contract_address, abi_path):

    provider = Web3(
        Web3.HTTPProvider(
            rpc_url,
            request_kwargs={"timeout": 5}
        )
    )

    connected = provider.is_connected()

    if not connected:
        return (
            False, False,
            "Hardhat RPC tidak dapat diakses.",
            None, None, 0, None
        )

    latest = provider.eth.block_number
    network_id = provider.eth.chain_id

    if not contract_address:
        return (
            True, False,
            "deployment.json belum ditemukan.",
            None, None, latest, network_id
        )

    try:
        with open(abi_path, "r", encoding="utf-8") as f:
            abi = json.load(f)["abi"]

        address = Web3.to_checksum_address(contract_address)

        code = provider.eth.get_code(address)

        if len(code) == 0:
            return (
                True, False,
                "Tidak ditemukan smart contract di alamat tersebut.",
                None, None, latest, network_id
            )

        instance = provider.eth.contract(
            address=address,
            abi=abi
        )

        creator = Web3.to_checksum_address(
            instance.functions.kreator().call()
        )

        platform = Web3.to_checksum_address(
            instance.functions.platformMusik().call()
        )

        return (
            True, True, None,
            creator, platform, latest, network_id
        )

    except Exception as e:
        return (
            True, False,
            f"Gagal menghubungkan smart contract: {e}",
            None, None, latest, network_id
        )


(
    rpc_connected,
    contract_ready,
    contract_error,
    creator_addr,
    platform_addr,
    latest_block,
    chain_id
) = load_chain_state(
    RPC_URL,
    CONTRACT_ADDRESS,
    str(ABI_PATH)
)

contract = None
ABI = []

if contract_ready:
    with open(ABI_PATH, "r", encoding="utf-8") as f:
        ABI = json.load(f)["abi"]

    contract = w3.eth.contract(
        address=Web3.to_checksum_address(CONTRACT_ADDRESS),
        abi=ABI
    )


# =========================================================
# 6. HELPER
# =========================================================

def esc(x):
    return htmllib.escape(str(x))


def short(addr, a=6, b=4):
    addr = str(addr)
    return addr if len(addr) <= a + b + 3 else f"{addr[:a]}…{addr[-b:]}"


def wei_to_eth(wei):
    return float(Web3.from_wei(int(wei), "ether"))


def fmt_eth(v):
    return f"{v:,.6f}".rstrip("0").rstrip(".") + " ETH" if v else "0 ETH"


def badge(status):
    fg, bg = STATUS_COLORS.get(str(status).upper(), ("#6b7280", "rgba(107,114,128,.15)"))
    return f'<span class="badge" style="color:{fg};background:{bg}">{esc(status)}</span>'


def hero(icon, title, subtitle):
    st.markdown(
        f'<div class="hero"><div class="hero-icon">{icon}</div>'
        f'<div><h1>{esc(title)}</h1><p>{esc(subtitle)}</p></div>'
        f'<div class="vinyl"></div></div>',
        unsafe_allow_html=True,
    )


def stat_card(icon, label, value, sub=""):
    st.markdown(
        f'<div class="stat-card"><div class="stat-top"><span class="stat-label">{esc(label)}</span>'
        f'<span class="stat-icon">{icon}</span></div>'
        f'<div class="stat-value">{esc(value)}</div>'
        f'<div class="stat-sub">{esc(sub)}</div></div>',
        unsafe_allow_html=True,
    )


def pill(text, kind="ok"):
    return f'<span class="pill pill-{kind}"><span class="dot"></span>{esc(text)}</span>'


def section(title):
    st.markdown(f'<div class="section-title">{esc(title)}</div>', unsafe_allow_html=True)


def info_card(rows):
    body = "".join(
        f'<div class="info-row"><span class="info-key">{esc(k)}</span>'
        f'<span class="info-val">{v}</span></div>'
        for k, v in rows
    )
    st.markdown(f'<div class="info-card">{body}</div>', unsafe_allow_html=True)


def donut_chart(labels, values, colors=None, height=300):
    if PLOTLY:
        fig = go.Figure(go.Pie(
            labels=labels, values=values, hole=0.62,
            marker=dict(colors=colors, line=dict(color="rgba(0,0,0,0)", width=0)),
            textinfo="label+percent", sort=False,
        ))
        fig.update_layout(
            height=height, margin=dict(l=10, r=10, t=10, b=10),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#1c1917", family="DM Sans"),
            legend=dict(orientation="h", y=-0.1),
        )
        st.plotly_chart(fig, **STRETCH)
    else:
        st.bar_chart({"Nilai": dict(zip(labels, values))})


def bar_chart(labels, values, colors=None, ytitle="ETH", height=300):
    if PLOTLY:
        fig = go.Figure(go.Bar(
            x=labels, y=values,
            marker=dict(color=colors or "#e4572e", cornerradius=6),
        ))
        fig.update_layout(
            height=height, margin=dict(l=10, r=10, t=10, b=10),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#1c1917", family="DM Sans"),
            yaxis_title=ytitle, xaxis_title=None,
        )
        fig.update_yaxes(gridcolor="rgba(28,25,23,.1)")
        st.plotly_chart(fig, **STRETCH)
    else:
        st.bar_chart(dict(zip(labels, values)))


def parse_music(m):
    return {
        "token_id": int(m[0]),
        "batch_id": m[1],
        "judul": m[2],
        "jenis": m[3],
        "pemilik": m[4],
        "royalti_wei": int(m[5]),
        "royalti_eth": wei_to_eth(m[5]),
        "status": m[6],
    }


def get_music(batch_id):
    try:
        m = contract.functions.getMusic(batch_id).call()
        if not m[1]:
            return None
        return parse_music(m)
    except Exception:
        return None


@st.cache_data(ttl=120, show_spinner=False)
def fetch_all_batches(_contract, address_key):
    """Membaca seluruh batch dari smart contract."""
    rows, misses, i = [], 0, 1

    while misses < 3 and i <= 300:
        try:
            m = _contract.functions.getMusic(
                f"MUSIC-{i}"
            ).call()

            if not m[1]:
                raise ValueError("kosong")

            rows.append(parse_music(m))
            misses = 0

        except Exception:
            misses += 1

        i += 1

    return rows


def get_history(batch_id):
    out = []
    try:
        n = contract.functions.getHistoryCount(batch_id).call()
        for i in range(n):
            h = contract.functions.getHistory(batch_id, i).call()
            out.append({
                "batch_id": h[0],
                "aktivitas": h[1],
                "ts": int(h[2]),
                "waktu": datetime.fromtimestamp(int(h[2])).strftime("%d-%m-%Y %H:%M:%S"),
                "pelaku": h[3],
            })
    except Exception:
        pass
    return out


def render_timeline(items):
    html_items = ""
    for it in items:
        html_items += (
            f'<div class="tl-item"><div class="tl-title">{esc(it["aktivitas"])}'
            f' <span style="opacity:.55;font-weight:500">· {esc(it["batch_id"])}</span></div>'
            f'<div class="tl-meta">🕒 {esc(it["waktu"])} &nbsp; 👤 {esc(short(it["pelaku"], 8, 6))}</div></div>'
        )
    st.markdown(f'<div class="timeline">{html_items}</div>', unsafe_allow_html=True)


batches = fetch_all_batches(contract, str(CONTRACT_ADDRESS)) if contract_ready else []
batch_ids = [b["batch_id"] for b in batches]


# ---------- Wallet (sidebar) ----------

with st.sidebar:
    st.markdown('<div class="side-brand">🎵 MusicRoyalty</div>', unsafe_allow_html=True)
    st.markdown('<div class="side-sub">Blockchain-Based Music Royalty</div>', unsafe_allow_html=True)

    wallet_result = wallet_component(
        key="musicroyalty_wallet",
        default={"wallet": {"address": "", "chainId": "", "connected": False}},
        on_wallet_change=lambda: None,
    )

wallet = wallet_result.get("wallet") or {"address": "", "chainId": "", "connected": False}
wallet_connected = bool(wallet.get("connected")) and wallet.get("address", "") != ""
address = Web3.to_checksum_address(wallet["address"]) if wallet_connected else None

wallet_chain_id = None
if wallet_connected:
    try:
        wallet_chain_id = int(wallet["chainId"], 16)
    except Exception:
        wallet_chain_id = None
network_ok = rpc_connected and wallet_chain_id is not None and wallet_chain_id == chain_id


def current_role():
    if not wallet_connected:
        return "Belum terhubung"
    if creator_addr and address.lower() == creator_addr.lower():
        return "Kreator"
    if platform_addr and address.lower() == platform_addr.lower():
        return "Platform Musik"
    return "Akun Lain"


def preflight(role=None):
    """Mengembalikan pesan error (str) bila belum siap, atau None bila siap."""
    if not contract_ready:
        return "Smart Contract belum terhubung."
    if not wallet_connected:
        return "Hubungkan MetaMask terlebih dahulu (tombol di sidebar)."
    if not network_ok:
        return "Pilih jaringan Hardhat Local (Chain ID 31337) di MetaMask."
    if role == "kreator" and creator_addr and address.lower() != creator_addr.lower():
        return f"Akun yang terhubung bukan Kreator. Gunakan akun: {creator_addr}"
    if role == "platform" and platform_addr and address.lower() != platform_addr.lower():
        return f"Akun yang terhubung bukan Platform Musik. Gunakan akun: {platform_addr}"
    return None


def prepare_tx(fn, action, pending_key, value_wei=0):
    calldata = fn._encode_transaction_data()
    st.session_state["req_id"] += 1
    tx = {
        "from": address,
        "to": Web3.to_checksum_address(CONTRACT_ADDRESS),
        "data": calldata,
        "chainId": chain_id,
        "requestId": st.session_state["req_id"],
        "action": action,
    }
    if value_wei:
        tx["value"] = hex(int(value_wei))
    st.session_state[pending_key] = tx


def tx_panel(key, pending_key, label, idle):
    """Tombol MetaMask + penanganan hasil transaksi (berhasil / gagal / menunggu)."""
    tx = st.session_state.get(pending_key)
    result = tx_component(
        key=key,
        data={"transaction": tx, "label": label, "idle": idle},
        default={"tx_submitted": None, "tx_error": None},
        on_tx_submitted_change=lambda: None,
        on_tx_error_change=lambda: None,
    )
    submitted = result.get("tx_submitted")
    error = result.get("tx_error")

    outcome = None
    if submitted and submitted.get("txHash"):
        tx_hash = submitted["txHash"]
        meta = st.session_state.get(pending_key) or {}
        st.session_state[pending_key] = None
        entry = {
            "Waktu": datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
            "Aksi": meta.get("action", "-"),
            "Tx Hash": tx_hash,
            "Status": "Menunggu",
            "Block": "-",
        }
        try:
            with st.spinner("⏳ Menunggu konfirmasi blok..."):
                receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            entry["Block"] = receipt.blockNumber
            if receipt.status == 1:
                entry["Status"] = "Berhasil"
                outcome = ("success", tx_hash, receipt)
            else:
                entry["Status"] = "Gagal"
                outcome = ("failed", tx_hash, receipt)
        except Exception as e:
            outcome = ("pending", tx_hash, str(e))
        if not any(x["Tx Hash"] == tx_hash for x in st.session_state["tx_log"]):
            st.session_state["tx_log"].insert(0, entry)
        st.session_state["tx_results"][key] = outcome
        fetch_all_batches.clear()
        outcome = st.session_state["tx_results"][key]
    elif error:
        st.session_state[pending_key] = None
        st.session_state["tx_results"][key] = ("error", error.get("message", "Transaksi gagal."), None)

    shown = st.session_state["tx_results"].get(key)
    if shown:
        kind, a, b = shown
        if kind == "success":
            st.success("✅ Transaksi berhasil dieksekusi smart contract.")
            c1, c2 = st.columns(2)
            c1.metric("Block Number", b.blockNumber)
            c2.metric("Gas Used", f"{b.gasUsed:,}")
            st.caption("Transaction Hash")
            st.code(a)
        elif kind == "failed":
            st.error("❌ Transaksi tercatat tetapi gagal dijalankan oleh smart contract (revert).")
            st.code(a)
        elif kind == "pending":
            st.warning("⏳ Transaksi sudah dikirim, tetapi receipt belum berhasil dibaca.")
            st.code(a)
            st.caption(b)
        else:
            st.error(f"❌ {a}")
    return shown


def parse_eth_amount(text):
    try:
        val = Decimal(text.strip())
    except (InvalidOperation, AttributeError):
        raise ValueError("Nominal harus berupa angka, contoh: 0.1")
    if val <= 0:
        raise ValueError("Nominal harus lebih dari 0.")
    if val.as_tuple().exponent < -18:
        raise ValueError("Maksimal 18 angka di belakang koma.")
    return val, int(w3.to_wei(val, "ether"))


def batch_picker(label, key):
    if batch_ids:
        default = st.session_state.get("selected_batch")
        idx = batch_ids.index(default) if default in batch_ids else 0
        return st.selectbox(label, batch_ids, index=idx, key=key)
    return st.text_input(label, placeholder="Contoh: MUSIC-1", key=key).strip()


def go_detail(bid):
    st.session_state["selected_batch"] = bid
    st.session_state["nav"] = PAGES[3]


def guard_contract():
    if not contract_ready:
        st.error(contract_error or "Smart Contract belum terhubung. Pastikan Hardhat node berjalan dan contract sudah di-deploy.")
        return False
    return True


# =========================================================
# 7. SIDEBAR NAVIGASI
# =========================================================

with st.sidebar:
    st.radio("Navigasi", PAGES, key="nav", label_visibility="collapsed")
    st.divider()

    st.markdown(
        pill("RPC Connected" if rpc_connected else "RPC Offline", "ok" if rpc_connected else "bad")
        + pill("Contract Ready" if contract_ready else "Contract Error", "ok" if contract_ready else "bad")
        + pill(
            f"Role: {current_role()}",
            "ok" if wallet_connected and network_ok else ("warn" if wallet_connected else "bad"),
        ),
        unsafe_allow_html=True,
    )
    if wallet_connected and not network_ok:
        st.caption("⚠️ Jaringan MetaMask belum sesuai dengan Hardhat Local.")
    st.caption("Hardhat · MetaMask · Streamlit · Web3.py")


# =========================================================
# 8. HALAMAN: DASHBOARD
# =========================================================

def page_dashboard():
    hero("🎵", "MusicRoyalty Dashboard",
         "Pencatatan karya musik, pembagian royalti, dan transparansi pembayaran di blockchain.")

    st.markdown(
        pill("Hardhat Blockchain Connected" if rpc_connected else "Hardhat RPC tidak dapat diakses", "ok" if rpc_connected else "bad")
        + pill("Smart Contract Terhubung" if contract_ready else "Smart Contract Belum Terhubung", "ok" if contract_ready else "bad")
        + pill("Wallet Terhubung" if wallet_connected else "Wallet Belum Terhubung", "ok" if wallet_connected else "warn"),
        unsafe_allow_html=True,
    )

    if not rpc_connected:
        st.error("Hardhat RPC tidak dapat diakses. Jalankan `npx hardhat node`.")
    if contract_error:
        st.error(contract_error)

    total_royalti = sum(b["royalti_eth"] for b in batches)
    owners = {b["pemilik"] for b in batches}

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        stat_card("🎼", "Jumlah Karya", len(batches), "Music batch tercatat")
    with c2:
        stat_card("💎", "Total Royalti", fmt_eth(total_royalti), "Akumulasi seluruh batch")
    with c3:
        stat_card("👥", "Jumlah Pencipta", len(owners), "Pemilik hak cipta unik")
    with c4:
        stat_card("⛓️", "Latest Block", f"{latest_block:,}", f"Chain ID {chain_id}" if chain_id else "-")

    st.write("")
    left, right = st.columns(2)
    with left:
        section("📊 Distribusi Status Karya")
        if batches:
            counts = {}
            for b in batches:
                counts[b["status"]] = counts.get(b["status"], 0) + 1
            donut_chart(list(counts.keys()), list(counts.values()),
                        [STATUS_COLORS.get(s.upper(), ("#6b7280",))[0] for s in counts])
        else:
            st.info("Belum ada karya. Buat batch pertama di halaman Register Music.")
    with right:
        section("💰 Royalti per Karya")
        if batches:
            bar_chart([b["batch_id"] for b in batches], [b["royalti_eth"] for b in batches])
        else:
            st.info("Belum ada data royalti.")

    section("🆕 Karya Terbaru")
    if batches:
        recent = list(reversed(batches))[:3]
        cols = st.columns(len(recent))
        for col, b in zip(cols, recent):
            with col:
                st.markdown(
                    f'<div class="music-card"><div class="mc-id">{esc(b["batch_id"])} · Token #{b["token_id"]}</div>'
                    f'<div class="mc-title">{esc(b["judul"])}</div>'
                    f'{badge(b["status"])}'
                    f'<div class="mc-row">🎧 {esc(b["jenis"])}</div>'
                    f'<div class="mc-row">💎 {esc(fmt_eth(b["royalti_eth"]))}</div></div>',
                    unsafe_allow_html=True,
                )
                st.button("Lihat detail", key=f"dash_{b['batch_id']}", on_click=go_detail,
                          args=(b["batch_id"],), **STRETCH)

    with st.expander("ℹ️ Informasi Smart Contract & Peserta Royalti"):
        info_card([
            ("RPC URL", f"<code>{esc(RPC_URL)}</code>"),
            ("Contract Address", f"<code>{esc(CONTRACT_ADDRESS or '-')}</code>"),
            ("Akun Kreator", f"<code>{esc(creator_addr or '-')}</code>"),
            ("Akun Platform Musik", f"<code>{esc(platform_addr or '-')}</code>"),
        ])
        st.write("")
        cols = st.columns(4)
        for col, (name, pct, _) in zip(cols, PARTICIPANTS):
            col.metric(name, f"{pct}%")


# =========================================================
# 9. HALAMAN: MUSIC CATALOG (DATA MANAGEMENT)
# =========================================================

def page_catalog():
    hero("📚", "Music Catalog", "Daftar karya musik yang dibaca langsung dari smart contract.")
    if not guard_contract():
        return

    top = st.columns([3, 2, 2, 1])
    query = top[0].text_input("🔍 Cari", placeholder="Cari judul, Batch ID, atau jenis...", label_visibility="collapsed")
    statuses = sorted({b["status"] for b in batches})
    status_filter = top[1].multiselect("Status", statuses, placeholder="Filter status", label_visibility="collapsed")
    view = top[2].radio("Tampilan", ["Tabel", "Kartu"], horizontal=True, label_visibility="collapsed")
    if top[3].button("🔄", help="Muat ulang data", **STRETCH):
        fetch_all_batches.clear()
        st.rerun()

    data = batches
    if query.strip():
        q = query.strip().lower()
        data = [b for b in data if q in b["judul"].lower() or q in b["batch_id"].lower() or q in b["jenis"].lower()]
    if status_filter:
        data = [b for b in data if b["status"] in status_filter]

    c1, c2, c3 = st.columns(3)
    c1.metric("Ditampilkan", f"{len(data)} / {len(batches)}")
    c2.metric("Total Royalti", fmt_eth(sum(b["royalti_eth"] for b in data)))
    c3.metric("Pencipta Unik", len({b["pemilik"] for b in data}))

    if not data:
        st.info("Tidak ada karya yang cocok. Daftarkan karya baru di halaman Register Music.")
        return

    if view == "Tabel":
        table = [{
            "Batch ID": b["batch_id"], "Token": b["token_id"], "Judul Musik": b["judul"],
            "Jenis Transaksi": b["jenis"], "Pemilik Hak Cipta": b["pemilik"],
            "Total Royalti (ETH)": b["royalti_eth"], "Status": b["status"],
        } for b in data]
        st.dataframe(
            table, hide_index=True, **STRETCH,
            column_config={
                "Total Royalti (ETH)": st.column_config.NumberColumn(format="%.6f"),
                "Pemilik Hak Cipta": st.column_config.TextColumn(width="medium"),
            },
        )
        st.download_button(
            "⬇️ Unduh CSV",
            "\n".join(
                [",".join(table[0].keys())]
                + [",".join(f'"{v}"' for v in r.values()) for r in table]
            ),
            file_name="music_catalog.csv", mime="text/csv",
        )
    else:
        cols = st.columns(3)
        for i, b in enumerate(data):
            with cols[i % 3]:
                st.markdown(
                    f'<div class="music-card"><div class="mc-id">{esc(b["batch_id"])} · Token #{b["token_id"]}</div>'
                    f'<div class="mc-title">{esc(b["judul"])}</div>{badge(b["status"])}'
                    f'<div class="mc-row">🎧 {esc(b["jenis"])}</div>'
                    f'<div class="mc-row">👤 {esc(short(b["pemilik"], 8, 6))}</div>'
                    f'<div class="mc-row">💎 {esc(fmt_eth(b["royalti_eth"]))}</div></div>',
                    unsafe_allow_html=True,
                )
                st.button("Lihat detail", key=f"cat_{b['batch_id']}", on_click=go_detail,
                          args=(b["batch_id"],), **STRETCH)


# =========================================================
# 10. HALAMAN: REGISTER MUSIC (FORM INPUT)
# =========================================================

def page_register():
    hero("📝", "Register Music", "Daftarkan karya musik baru dan catat penggunaannya melalui MetaMask.")
    tab_new, tab_usage = st.tabs(["🎼 Buat Music Batch", "🎧 Catat Penggunaan Musik"])

    with tab_new:
        st.caption("Hanya dapat dijalankan oleh akun Kreator (Hardhat Account #0).")
        left, right = st.columns([3, 2], gap="large")

        with left:
            with st.form("create_music_batch_form"):
                music_title = st.text_input("Judul Musik *", placeholder="Contoh: Senja di Cirebon", max_chars=100)
                jenis_sel = st.selectbox("Jenis Transaksi *", USAGE_TYPES)
                jenis_custom = st.text_input("Jenis lainnya (isi bila memilih 'Lainnya')", max_chars=50)
                prepare = st.form_submit_button("Siapkan Transaksi", type="primary")

        with right:
            st.markdown("**🔐 Hash File Audio (opsional)**")
            audio = st.file_uploader("Unggah file audio", type=["mp3", "wav", "flac", "ogg", "m4a"],
                                     label_visibility="collapsed")
            if audio is not None:
                raw = audio.getvalue()
                st.audio(raw)
                st.caption(f"{audio.name} · {len(raw) / 1024:,.1f} KB · SHA-256")
                st.code("0x" + hashlib.sha256(raw).hexdigest())
                st.caption("Hash dihitung di aplikasi sebagai bukti keaslian file. "
                           "Fungsi createBatch pada contract ini tidak menyimpan hash.")

        if prepare:
            jenis = jenis_custom.strip() if jenis_sel == "Lainnya" else jenis_sel
            title = music_title.strip()
            err = None
            if len(title) < 3:
                err = "Judul musik minimal 3 karakter."
            elif not jenis:
                err = "Jenis transaksi wajib diisi."
            else:
                err = preflight("kreator")
            if err:
                st.error(err)
            else:
                try:
                    prepare_tx(contract.functions.createBatch(title, jenis),
                               f"Create Batch: {title}", "pending_create_tx")
                    st.success("Transaksi siap. Klik tombol MetaMask di bawah untuk melanjutkan.")
                except Exception as e:
                    st.error("Tidak dapat menyiapkan transaksi.")
                    st.code(str(e))

        tx_panel("tx_create_batch", "pending_create_tx", "Konfirmasi Create Batch",
                 "Isi form lalu klik Siapkan Transaksi.")
        if st.session_state["tx_results"].get("tx_create_batch", (None,))[0] == "success":
            st.info("Batch baru dapat dicari di Music Catalog (ID dibuat otomatis, mis. MUSIC-1).")

    with tab_usage:
        st.caption("Mencatat penggunaan musik akan mengubah status batch menjadi USED.")
        if not guard_contract():
            return
        if not batch_ids:
            st.info("Belum ada Music Batch. Buat batch terlebih dahulu.")
        usage_batch = batch_picker("Music Batch ID *", "usage_batch")
        usage_sel = st.selectbox("Jenis Penggunaan Musik *", USAGE_TYPES, key="usage_type")
        usage_custom = ""
        if usage_sel == "Lainnya":
            usage_custom = st.text_input("Sebutkan jenis penggunaan", max_chars=50, key="usage_custom")

        if st.button("Siapkan Pencatatan", type="primary", key="prep_usage"):
            jenis = usage_custom.strip() if usage_sel == "Lainnya" else usage_sel
            err = None
            if not usage_batch:
                err = "Batch ID wajib diisi."
            elif not jenis:
                err = "Jenis penggunaan wajib diisi."
            else:
                err = preflight()
                if not err and get_music(usage_batch) is None:
                    err = f"Batch '{usage_batch}' tidak ditemukan di blockchain."
            if err:
                st.error(err)
            else:
                try:
                    prepare_tx(contract.functions.recordMusicUsage(usage_batch, jenis),
                               f"Record Usage: {usage_batch}", "pending_usage_tx")
                    st.success("Transaksi siap. Klik tombol MetaMask di bawah.")
                except Exception as e:
                    st.error("Tidak dapat menyiapkan transaksi.")
                    st.code(str(e))

        tx_panel("tx_usage", "pending_usage_tx", "Konfirmasi Pencatatan Penggunaan",
                 "Pilih batch lalu klik Siapkan Pencatatan.")


# =========================================================
# 11. HALAMAN: MUSIC DETAIL
# =========================================================

def page_detail():
    hero("🔎", "Music Detail", "Informasi karya, pemilik, persentase royalti, dan riwayat aktivitas berdasarkan ID.")
    if not guard_contract():
        return

    c1, c2 = st.columns([2, 2])
    with c1:
        chosen = batch_picker("Pilih Music Batch", "detail_select")
    with c2:
        manual = st.text_input("Atau ketik Batch ID", placeholder="Contoh: MUSIC-1", key="detail_manual")
    bid = manual.strip() or chosen
    if not bid:
        st.info("Belum ada batch yang dipilih.")
        return

    music = get_music(bid)
    if music is None:
        st.error(f"Music Batch '{bid}' tidak ditemukan di blockchain.")
        return
    st.session_state["selected_batch"] = bid

    left, right = st.columns([3, 2], gap="large")
    with left:
        st.markdown(f"## {esc(music['judul'])}")
        info_card([
            ("Batch ID", esc(music["batch_id"])),
            ("Token ID", f"#{music['token_id']}"),
            ("Jenis Transaksi", esc(music["jenis"])),
            ("Pemilik Hak Cipta", f"<code>{esc(music['pemilik'])}</code>"),
            ("Total Royalti", esc(fmt_eth(music["royalti_eth"])) + f" <span style='opacity:.5'>({music['royalti_wei']:,} wei)</span>"),
            ("Status", badge(music["status"])),
        ])
    with right:
        st.markdown("**Persentase Kepemilikan Royalti**")
        donut_chart([p[0] for p in PARTICIPANTS], [p[1] for p in PARTICIPANTS], [p[2] for p in PARTICIPANTS], height=290)

    tab_split, tab_hist = st.tabs(["💸 Pembagian Royalti", "📜 Riwayat Aktivitas"])
    with tab_split:
        total = music["royalti_eth"]
        cols = st.columns(4)
        for col, (name, pct, _) in zip(cols, PARTICIPANTS):
            col.metric(name, f"{pct}%", fmt_eth(total * pct / 100) if total else "Belum didistribusikan")
        if not total:
            st.caption("Total royalti masih 0. Lakukan Royalty Distribution untuk menghitung pembagian.")
    with tab_hist:
        hist = get_history(bid)
        if hist:
            render_timeline(hist)
        else:
            st.info("Belum ada riwayat aktivitas.")


# =========================================================
# 12. HALAMAN: ROYALTY DISTRIBUTION
# =========================================================

def page_royalty():
    hero("💰", "Royalty Distribution", "Simulasikan, distribusikan, dan bayarkan royalti melalui akun Platform Musik.")
    tab_sim, tab_dist, tab_pay = st.tabs(["🧮 Simulasi", "📊 1. Distribusi", "💸 2. Pembayaran"])

    with tab_sim:
        st.caption("Simulasi tidak mengirim transaksi apa pun.")
        amount = st.number_input("Total Royalti (ETH)", min_value=0.0, value=1.0, step=0.1, format="%.4f", key="sim_amount")
        c1, c2 = st.columns([2, 3], gap="large")
        with c1:
            for name, pct, _ in PARTICIPANTS:
                st.metric(f"{name} ({pct}%)", fmt_eth(amount * pct / 100))
        with c2:
            donut_chart([p[0] for p in PARTICIPANTS], [amount * p[1] / 100 for p in PARTICIPANTS],
                        [p[2] for p in PARTICIPANTS])

    with tab_dist:
        st.caption("Menghitung pembagian royalti. Status batch menjadi DISTRIBUTED.")
        if not guard_contract():
            return
        dist_batch = batch_picker("Music Batch ID *", "dist_batch")
        dist_amount = st.text_input("Total Royalti (ETH) *", placeholder="Contoh: 0.1", key="dist_amount")

        if st.button("Siapkan Transaksi Distribusi", type="primary", key="prep_dist"):
            err = None
            try:
                if not dist_batch:
                    err = "Batch ID wajib diisi."
                else:
                    err = preflight("platform")
                    if not err and get_music(dist_batch) is None:
                        err = f"Batch '{dist_batch}' tidak ditemukan di blockchain."
                    if not err:
                        eth_val, wei_val = parse_eth_amount(dist_amount)
                        prepare_tx(contract.functions.distributeRoyalty(dist_batch, wei_val),
                                   f"Distribute Royalty: {dist_batch}", "pending_dist_tx")
                        st.success(f"Transaksi siap · {eth_val} ETH = {wei_val:,} wei")
            except ValueError as e:
                err = str(e)
            except Exception as e:
                err = f"Tidak dapat menyiapkan transaksi: {e}"
            if err:
                st.error(err)

        res = tx_panel("tx_distribute", "pending_dist_tx", "Konfirmasi Royalty Distribution",
                       "Isi form lalu klik Siapkan Transaksi Distribusi.")
        if res and res[0] == "success":
            st.markdown("**Pembagian royalti berdasarkan smart contract:**")
            cols = st.columns(4)
            for col, (name, pct, _) in zip(cols, PARTICIPANTS):
                col.metric(name, f"{pct}%")
            st.session_state["selected_batch"] = dist_batch

    with tab_pay:
        st.caption("Mengirim ETH ke smart contract untuk dibayarkan kepada seluruh peserta. Status batch menjadi COMPLETED.")
        if not guard_contract():
            return
        pay_batch = batch_picker("Music Batch ID *", "pay_batch")
        music = get_music(pay_batch) if pay_batch else None
        default_amount = ""
        if music:
            c1, c2 = st.columns(2)
            c1.metric("Status Batch", music["status"])
            c2.metric("Total Royalti Tercatat", fmt_eth(music["royalti_eth"]))
            if music["royalti_eth"] > 0:
                default_amount = str(Web3.from_wei(music["royalti_wei"], "ether"))
        pay_amount = st.text_input("Total Pembayaran (ETH) *", value=default_amount,
                                   placeholder="Contoh: 0.1", key=f"pay_amount_{pay_batch}")

        if st.button("Siapkan Pembayaran", type="primary", key="prep_pay"):
            err = None
            try:
                if not pay_batch:
                    err = "Batch ID wajib diisi."
                else:
                    err = preflight("platform")
                    if not err and music is None:
                        err = f"Batch '{pay_batch}' tidak ditemukan di blockchain."
                    if not err:
                        eth_val, wei_val = parse_eth_amount(pay_amount)
                        prepare_tx(contract.functions.payRoyalty(pay_batch),
                                   f"Pay Royalty: {pay_batch}", "pending_pay_tx", value_wei=wei_val)
                        st.success(f"Transaksi siap · {eth_val} ETH")
            except ValueError as e:
                err = str(e)
            except Exception as e:
                err = f"Gagal menyiapkan pembayaran: {e}"
            if err:
                st.error(err)

        res = tx_panel("tx_pay", "pending_pay_tx", "Konfirmasi Pay Royalty",
                       "Siapkan pembayaran terlebih dahulu.")
        if res and res[0] == "success":
            st.session_state["selected_batch"] = pay_batch


# =========================================================
# 13. HALAMAN: ROYALTY HISTORY
# =========================================================

def page_history():
    hero("📜", "Royalty History", "Riwayat aktivitas dan transaksi royalti yang tercatat di smart contract.")
    if not guard_contract():
        return
    if not batch_ids:
        st.info("Belum ada Music Batch.")
        return

    options = ["Semua Batch"] + batch_ids
    sel = st.selectbox("Filter Batch", options)
    targets = batch_ids if sel == "Semua Batch" else [sel]

    items = []
    for bid in targets:
        items.extend(get_history(bid))
    items.sort(key=lambda x: x["ts"], reverse=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Aktivitas", len(items))
    c2.metric("Batch Dicakup", len(targets))
    c3.metric("Aktivitas Terakhir", items[0]["waktu"] if items else "-")

    if not items:
        st.info("Belum ada riwayat aktivitas.")
        return

    tab_tl, tab_tbl = st.tabs(["🕒 Timeline", "📋 Tabel"])
    with tab_tl:
        render_timeline(items)
    with tab_tbl:
        st.dataframe(
            [{"Batch ID": i["batch_id"], "Aktivitas": i["aktivitas"], "Waktu": i["waktu"], "Pelaku": i["pelaku"]} for i in items],
            hide_index=True, **STRETCH,
        )


# =========================================================
# 14. HALAMAN: WALLET & TRANSACTION
# =========================================================

def page_wallet():
    hero("👛", "Wallet & Transaction", "Alamat wallet, saldo, hak akses akun, dan status transaksi.")

    if not wallet_connected:
        st.info("Klik **Connect MetaMask** di sidebar untuk menghubungkan wallet.")
    else:
        c1, c2, c3 = st.columns(3)
        with c1:
            stat_card("🦊", "Role Akun", current_role(), "Berdasarkan smart contract")
        with c2:
            stat_card("🌐", "Wallet Chain ID", wallet_chain_id if wallet_chain_id is not None else "-",
                      "Sesuai Hardhat Local" if network_ok else "Tidak sesuai")
        with c3:
            bal = wei_to_eth(w3.eth.get_balance(address)) if rpc_connected else 0
            stat_card("💎", "ETH Balance", f"{bal:,.4f} ETH", "Saldo akun terhubung")

        st.write("")
        st.caption("Wallet Address")
        st.code(address)
        if network_ok:
            st.success("Jaringan wallet sesuai dengan Hardhat Local.")
        else:
            st.warning("Pilih jaringan Hardhat Local (Chain ID 31337) di MetaMask.")

    section("🔐 Akun Peran pada Smart Contract")
    info_card([
        ("Kreator", f"<code>{esc(creator_addr or '-')}</code>"),
        ("Platform Musik", f"<code>{esc(platform_addr or '-')}</code>"),
        ("Contract Address", f"<code>{esc(CONTRACT_ADDRESS or '-')}</code>"),
    ])

    section("🧾 Riwayat Transaksi Sesi Ini")
    log = st.session_state["tx_log"]
    if log:
        st.dataframe(log, hide_index=True, **STRETCH)
        latest = log[0]
        st.caption("Transaction Hash terakhir")
        st.code(latest["Tx Hash"])
        if st.button("Bersihkan riwayat sesi"):
            st.session_state["tx_log"] = []
            st.rerun()
    else:
        st.info("Belum ada transaksi pada sesi ini. Transaksi dari form Register Music dan Royalty Distribution akan muncul di sini.")


# =========================================================
# 15. ROUTER
# =========================================================

ROUTES = {
    PAGES[0]: page_dashboard,
    PAGES[1]: page_catalog,
    PAGES[2]: page_register,
    PAGES[3]: page_detail,
    PAGES[4]: page_royalty,
    PAGES[5]: page_history,
    PAGES[6]: page_wallet,
}
ROUTES[st.session_state["nav"]]()

st.divider()
st.caption("MusicRoyalty · Hardhat · MetaMask · Streamlit · Web3.py")
