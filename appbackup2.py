
import streamlit as st
import streamlit.components.v2 as components
import json
from pathlib import Path
from datetime import datetime
from web3 import Web3

# =========================================================
# 1. KONFIGURASI
# =========================================================

RPC_URL = "http://127.0.0.1:8545"

# GANTI DENGAN CONTRACT ADDRESS TERBARU
DEPLOYMENT_PATH = Path(__file__).parent / "deployment.json"

if DEPLOYMENT_PATH.exists():
    with open(DEPLOYMENT_PATH, "r") as file:
        deployment_data = json.load(file)

    CONTRACT_ADDRESS = deployment_data["contractAddress"]
else:
    CONTRACT_ADDRESS = None

ABI_PATH = (
    Path(__file__).parent
    / "artifacts"
    / "contracts"
    / "MusicRoyalty.sol"
    / "MusicRoyalty.json"
)

st.set_page_config(
    page_title="MusicRoyalty Dashboard",
    page_icon="🎵",
    layout="wide",
)

st.title("🎵 MusicRoyalty Dashboard")
st.caption("Blockchain-Based Music Royalty Management System")


# =========================================================
# 2. KOMPONEN METAMASK
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

        const connected = accounts && accounts.length > 0;

        setStateValue("wallet", {
            address: connected ? accounts[0] : "",
            chainId: chainId,
            connected: connected
        });

        status.textContent = connected
            ? "Wallet terhubung: " + accounts[0]
            : "Wallet belum terhubung.";
    }

    async function connectWallet() {
        if (!window.ethereum) {
            status.textContent = "MetaMask tidak ditemukan.";
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
# 3. KONEKSI BLOCKCHAIN
# =========================================================

st.divider()
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
# 4. MEMBACA ABI DAN SMART CONTRACT
# =========================================================

contract = None
contract_ready = False

if not ABI_PATH.exists():
    st.error(f"File ABI tidak ditemukan: {ABI_PATH}")

elif not CONTRACT_ADDRESS:
    st.error("deployment.json belum ditemukan. Deploy contract terlebih dahulu.")

elif rpc_connected:
    try:
        with open(ABI_PATH, "r", encoding="utf-8") as file:
            contract_json = json.load(file)

        ABI = contract_json["abi"]

        contract = w3.eth.contract(
            address=Web3.to_checksum_address(CONTRACT_ADDRESS),
            abi=ABI,
        )

        # Memastikan alamat tersebut memiliki kode kontrak
        contract_code = w3.eth.get_code(
            Web3.to_checksum_address(CONTRACT_ADDRESS)
        )

        if len(contract_code) > 0:
            contract_ready = True
            st.success("Smart Contract MusicRoyalty terhubung.")
        else:
            st.error("Tidak ditemukan smart contract di alamat tersebut.")

    except Exception as error:
        st.error("Gagal menghubungkan smart contract.")
        st.code(str(error))


# =========================================================
# 5. CONNECT METAMASK
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

wallet = wallet_result.get(
    "wallet",
    {
        "address": "",
        "chainId": "",
        "connected": False,
    },
)

wallet_connected = (
    wallet.get("connected", False)
    and wallet.get("address", "") != ""
)

if wallet_connected:
    address = Web3.to_checksum_address(wallet["address"])

    st.success("Wallet berhasil terhubung.")

    st.caption("Wallet Address")
    st.code(address)

    try:
        wallet_chain_id = int(wallet["chainId"], 16)

        col1, col2 = st.columns(2)

        col1.metric("Wallet Chain ID", wallet_chain_id)

        if rpc_connected and wallet_chain_id == w3.eth.chain_id:
            st.success("Jaringan wallet sesuai dengan Hardhat Local.")
        else:
            st.warning("Pilih jaringan Hardhat Local di MetaMask.")

        if rpc_connected:
            balance = w3.eth.get_balance(address)
            balance_eth = w3.from_wei(balance, "ether")

            col2.metric(
                "ETH Balance",
                f"{float(balance_eth):.6f} ETH",
            )

    except Exception as error:
        st.error("Gagal membaca informasi wallet.")
        st.caption(str(error))

else:
    st.info("Klik Connect MetaMask untuk menghubungkan wallet.")


# =========================================================
# 6. MUSIC BATCH
# =========================================================

st.divider()
st.subheader("3. Music Batch")

st.write(
    "Masukkan Batch ID untuk melihat data musik "
    "yang tersimpan di blockchain."
)

batch_id = st.text_input(
    "Music Batch ID",
    placeholder="Contoh: MUSIC-1",
)

if st.button("Cari Music Batch"):
    if not contract_ready:
        st.error("Smart Contract belum terhubung.")

    elif not batch_id.strip():
        st.warning("Masukkan Batch ID terlebih dahulu.")

    else:
        try:
            music = contract.functions.getMusic(
                batch_id.strip()
            ).call()

            if not music[7]:
                st.warning("Music Batch tidak ditemukan.")

            else:
                st.success("Music Batch ditemukan!")

                st.markdown("### Informasi Musik")

                music_data = {
                    "Token ID": str(music[0]),
                    "Batch ID": music[1],
                    "Judul Musik": music[2],
                    "Jenis Transaksi": music[3],
                    "Pemilik Hak Cipta": music[4],
                    "Total Royalti": str(music[5]),
                    "Status": music[6],
                }

                st.table(
                    {
                        "Informasi": list(music_data.keys()),
                        "Nilai": list(music_data.values()),
                    }
                )

                st.session_state["selected_batch"] = batch_id.strip()

        except Exception as error:
            st.error("Gagal membaca Music Batch.")
            st.code(str(error))


# =========================================================
# 7. ROYALTY DISTRIBUTION
# =========================================================

st.divider()
st.subheader("4. Royalty Distribution")

if st.button("Lihat Pembagian Royalti"):
    selected_batch = st.session_state.get("selected_batch")

    if not contract_ready:
        st.error("Smart Contract belum terhubung.")

    elif not selected_batch:
        st.warning("Cari Music Batch terlebih dahulu.")

    else:
        try:
            distribution = contract.functions.getRoyaltyDistribution(
                selected_batch
            ).call()

            royalty_data = {
                "Kreator": distribution[0],
                "Produser": distribution[1],
                "Penulis Lagu": distribution[2],
                "Platform Musik": distribution[3],
            }

            st.success("Data pembagian royalti berhasil dibaca.")

            st.table(
                {
                    "Penerima": list(royalty_data.keys()),
                    "Jumlah Royalti": [
                        str(value) for value in royalty_data.values()
                    ],
                }
            )

            st.caption(
                "Persentase pembagian: Kreator 60%, "
                "Produser 20%, Penulis Lagu 15%, "
                "Platform Musik 5%."
            )

        except Exception as error:
            st.error("Gagal membaca pembagian royalti.")
            st.code(str(error))


# =========================================================
# 8. TRANSACTION HISTORY
# =========================================================

st.divider()
st.subheader("5. Transaction History")

if st.button("Lihat Riwayat Aktivitas"):
    selected_batch = st.session_state.get("selected_batch")

    if not contract_ready:
        st.error("Smart Contract belum terhubung.")

    elif not selected_batch:
        st.warning("Cari Music Batch terlebih dahulu.")

    else:
        try:
            history_count = contract.functions.getHistoryCount(
                selected_batch
            ).call()

            if history_count == 0:
                st.info("Belum ada riwayat aktivitas.")

            else:
                st.success(
                    f"Ditemukan {history_count} aktivitas."
                )

                for index in range(history_count):
                    history = contract.functions.getHistory(
                        selected_batch,
                        index,
                    ).call()

                    waktu = datetime.fromtimestamp(
                        int(history[2])
                    ).strftime("%d-%m-%Y %H:%M:%S")

                    with st.expander(
                        f"Aktivitas {index + 1}: {history[1]}"
                    ):
                        st.write("Batch ID:", history[0])
                        st.write("Aktivitas:", history[1])
                        st.write("Waktu:", waktu)
                        st.write("Pelaku:", history[3])

        except Exception as error:
            st.error("Gagal membaca riwayat aktivitas.")
            st.code(str(error))


# =========================================================
# 9. MUSIC ROYALTY FEATURES
# =========================================================

st.divider()
st.subheader("6. Music Royalty Management")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🎼 Music Batch")
    st.caption("Melihat informasi dan status musik.")

    st.markdown("### 📊 Royalty Distribution")
    st.caption("Melihat pembagian royalti.")

with col2:
    st.markdown("### 👥 Participants")
    st.caption("Kreator, produser, penulis lagu, dan platform.")

    st.markdown("### 📜 Transaction History")
    st.caption("Melihat riwayat aktivitas musik.")


# =========================================================
# 10. FOOTER
# =========================================================

st.divider()

st.caption(
    "MusicRoyalty | Hardhat | MetaMask | Streamlit | Web3.py"
)
