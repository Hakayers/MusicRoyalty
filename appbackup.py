
import streamlit as st
import streamlit.components.v2 as components
from web3 import Web3

# =========================================================
# KONFIGURASI MUSIC ROYALTY
# =========================================================

RPC_URL = "http://127.0.0.1:8545"

st.set_page_config(
    page_title="MusicRoyalty Dashboard",
    page_icon="🎵",
    layout="centered",
)

st.title("🎵 MusicRoyalty Dashboard")
st.caption(
    "Blockchain-Based Music Royalty Management System"
)

# =========================================================
# KOMPONEN JAVASCRIPT UNTUK METAMASK
# =========================================================

WALLET_HTML = """
<div>
  <button id="connect-wallet" type="button">
    Connect MetaMask
  </button>
  <p id="wallet-status">Wallet belum terhubung.</p>
</div>
"""

WALLET_CSS = """
button {
    padding: 0.7rem 1rem;
    border: none;
    border-radius: 8px;
    background: var(--st-primary-color);
    color: white;
    font-weight: 600;
    cursor: pointer;
}

p {
    color: var(--st-text-color);
    overflow-wrap: anywhere;
}
"""

WALLET_JS = """
export default function(component) {
    const { parentElement, setStateValue } = component;

    const button = parentElement.querySelector("#connect-wallet");
    const status = parentElement.querySelector("#wallet-status");

    let mounted = true;

    async function readWallet() {
        if (!window.ethereum) return;

        const accounts = await window.ethereum.request({
            method: "eth_accounts"
        });

        const chainId = await window.ethereum.request({
            method: "eth_chainId"
        });

        if (!mounted) return;

        if (accounts && accounts.length > 0) {
            setStateValue("wallet", {
                address: accounts[0],
                chainId: chainId,
                connected: true
            });

            status.textContent =
                "Wallet terhubung: " + accounts[0];
        } else {
            setStateValue("wallet", {
                address: "",
                chainId: chainId,
                connected: false
            });

            status.textContent = "Wallet belum terhubung.";
        }
    }

    async function connectWallet() {
        if (!window.ethereum) {
            status.textContent =
                "MetaMask tidak ditemukan.";
            return;
        }

        try {
            status.textContent =
                "Menunggu persetujuan MetaMask...";

            await window.ethereum.request({
                method: "eth_requestAccounts"
            });

            await readWallet();

        } catch (error) {
            status.textContent =
                "Koneksi gagal: " + error.message;
        }
    }

    function onAccountsChanged(accounts) {
        if (!mounted) return;

        window.ethereum.request({
            method: "eth_chainId"
        }).then((chainId) => {
            if (!mounted) return;

            setStateValue("wallet", {
                address: accounts.length > 0 ? accounts[0] : "",
                chainId: chainId,
                connected: accounts.length > 0
            });

            status.textContent = accounts.length > 0
                ? "Wallet terhubung: " + accounts[0]
                : "Akun tidak terhubung.";
        }).catch(() => {});
    }

    function onChainChanged(chainId) {
        if (!mounted) return;

        window.ethereum.request({
            method: "eth_accounts"
        }).then((accounts) => {
            if (!mounted) return;

            setStateValue("wallet", {
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
            window.ethereum.removeListener(
                "accountsChanged", onAccountsChanged
            );
            window.ethereum.removeListener(
                "chainChanged", onChainChanged
            );
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

# =========================================================
# 1. STATUS BLOCKCHAIN
# =========================================================

st.subheader("1. Blockchain Status")

w3 = Web3(
    Web3.HTTPProvider(
        RPC_URL,
        request_kwargs={"timeout": 5},
    )
)

rpc_connected = w3.is_connected()

if rpc_connected:
    st.success("Hardhat Blockchain Connected")

    col1, col2 = st.columns(2)

    col1.metric("Chain ID", w3.eth.chain_id)
    col2.metric("Latest Block", w3.eth.block_number)

    st.code(RPC_URL)

else:
    st.error(
        "Hardhat RPC tidak dapat diakses. "
        "Jalankan npx hardhat node."
    )

# =========================================================
# 2. CONNECT METAMASK
# =========================================================

st.divider()
st.subheader("2. Connect MetaMask")
 
wallet_result = wallet_component(
    key="musicroyalty_wallet",
    default={
        "wallet": {
            "address": "",
            "chainId": "",
            "connected": False,
        }
    },
    on_wallet_change=lambda: None,
)

wallet = wallet_result.wallet

# =========================================================
# 3. WALLET INFORMATION
# =========================================================

st.divider()
st.subheader("3. Wallet Information")

if wallet and wallet.get("connected") and wallet.get("address"):

    address = Web3.to_checksum_address(wallet["address"])

    st.success("Wallet berhasil terhubung.")

    st.caption("Wallet Address")
    st.code(address)

    try:
        wallet_chain_id = int(wallet["chainId"], 16)

        col1, col2 = st.columns(2)

        col1.metric("Wallet Chain ID", wallet_chain_id)

        if not rpc_connected:
            st.warning("RPC belum tersedia.")

        elif wallet_chain_id != w3.eth.chain_id:
            st.warning(
                "Pilih jaringan Hardhat Local di MetaMask."
            )

        else:
            st.success("Jaringan wallet sesuai.")

            if st.button("Check ETH Balance", type="primary"):
                balance_wei = w3.eth.get_balance(address)

                balance_eth = w3.from_wei(
                    balance_wei,
                    "ether",
                )

                col2.metric(
                    "ETH Balance",
                    f"{float(balance_eth):.6f} ETH",
                )

    except (ValueError, TypeError) as error:
        st.error("Chain ID tidak valid.")
        st.caption(str(error))

else:
    st.info(
        "Klik Connect MetaMask untuk menghubungkan wallet."
    )

# =========================================================
# 4. MUSIC ROYALTY FEATURES
# =========================================================

st.divider()
st.subheader("4. Music Royalty Management")

st.info(
    "Fitur pengelolaan musik dan royalti akan "
    "diintegrasikan dengan smart contract MusicRoyalty."
)

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🎼 Music Batch")
    st.caption("Create and view music batches.")

    st.markdown("### 📊 Royalty Distribution")
    st.caption("View royalty allocation.")

with col2:
    st.markdown("### 👥 Participants")
    st.caption("View royalty participants.")

    st.markdown("### 📜 Transaction History")
    st.caption("View music activity.")

# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "MusicRoyalty | Local Blockchain Practicum "
    "using Hardhat, MetaMask, Streamlit and Web3.py."
)
