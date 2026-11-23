
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
# KOMPONEN TRANSAKSI METAMASK
# =========================================================

TX_HTML = """
<div>
    <button id="send-transaction" type="button" disabled>
        Menunggu data transaksi...
    </button>
    <p id="transaction-status">Isi form terlebih dahulu.</p>
</div>
"""

TX_CSS = """
button {
    padding: 0.7rem 1rem;
    border: none;
    border-radius: 8px;
    background: var(--st-primary-color);
    color: white;
    font-weight: 600;
    cursor: pointer;
}

button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}
p {
    color: var(--st-text-color);
    overflow-wrap: anywhere;
}
"""

TX_JS = """
export default function(component) {
    const { parentElement, data, setTriggerValue } = component;
    const button = parentElement.querySelector("#send-transaction");
    const status = parentElement.querySelector("#transaction-status");
    let mounted = true;

    const tx = data && data.transaction ? data.transaction : null;

    if (tx && tx.to && tx.data && tx.from) {
        button.disabled = false;
        button.textContent = "Konfirmasi melalui MetaMask";
        status.textContent = "Transaksi siap dikirim. Periksa akun dan detail transaksi di MetaMask.";
    } else {
        button.disabled = true;
        button.textContent = "Menunggu data transaksi...";
        status.textContent = "Isi form Create Music Batch terlebih dahulu.";
    }

    async function sendTransaction() {
        if (!tx) return;

        if (!window.ethereum) {
            status.textContent = "MetaMask tidak ditemukan.";
            setTriggerValue("tx_error", {message: "MetaMask tidak ditemukan."});
            return;
        }

        button.disabled = true;
        status.textContent = "Memeriksa akun dan jaringan MetaMask...";

        try {
            const accounts = await window.ethereum.request({
                method: "eth_requestAccounts"
            });
            const chainId = await window.ethereum.request({
                method: "eth_chainId"
            });

            if (!accounts || accounts.length === 0) {
                throw new Error("Hubungkan akun MetaMask terlebih dahulu.");
            }
            if (accounts[0].toLowerCase() !== tx.from.toLowerCase()) {
                throw new Error("Akun MetaMask berubah. Pilih kembali akun kreator yang terhubung di dashboard.");
            }
            if (parseInt(chainId, 16) !== Number(tx.chainId)) {
                throw new Error("Jaringan MetaMask tidak sesuai. Pilih Hardhat Local (Chain ID 31337).");
            }

            status.textContent = "Menunggu konfirmasi transaksi di MetaMask...";
            const txHash = await window.ethereum.request({
                method: "eth_sendTransaction",
                params: [{
                    from: tx.from,
                    to: tx.to,
                    data: tx.data
                }]
            });

            status.textContent = "Transaksi dikirim: " + txHash;
            if (mounted) {
                setTriggerValue("tx_submitted", {
                    txHash: txHash,
                    requestId: tx.requestId
                });
            }
        } catch (error) {
            status.textContent = "Transaksi gagal: " + error.message;
            if (mounted) {
                setTriggerValue("tx_error", {message: error.message});
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
    name="musicroyalty_transaction",
    html=TX_HTML,
    css=TX_CSS,
    js=TX_JS,
)

# =========================================================
# KOMPONEN TRANSAKSI ROYALTY DISTRIBUTION
# =========================================================

ROYALTY_TX_HTML = """
<div>
    <button id="send-royalty-transaction" type="button" disabled>
        Menunggu data transaksi...
    </button>
    <p id="royalty-transaction-status">
        Isi form Royalty Distribution terlebih dahulu.
    </p>
</div>
"""

ROYALTY_TX_CSS = """
button {
    padding: 0.7rem 1rem;
    border: none;
    border-radius: 8px;
    background: var(--st-primary-color);
    color: white;
    font-weight: 600;
    cursor: pointer;
}

button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

p {
    color: var(--st-text-color);
    overflow-wrap: anywhere;
}
"""

ROYALTY_TX_JS = """
export default function(component) {
    const { parentElement, data, setTriggerValue } = component;

    const button = parentElement.querySelector(
        "#send-royalty-transaction"
    );
    const status = parentElement.querySelector(
        "#royalty-transaction-status"
    );

    let mounted = true;

    const tx = data && data.transaction
        ? data.transaction
        : null;

    if (tx && tx.to && tx.data && tx.from) {
        button.disabled = false;
        button.textContent =
            "Konfirmasi Royalty Distribution melalui MetaMask";

        status.textContent =
            "Transaksi siap dikirim. Periksa akun dan detail transaksi.";
    } else {
        button.disabled = true;
        button.textContent = "Menunggu data transaksi...";

        status.textContent =
            "Isi form Royalty Distribution terlebih dahulu.";
    }

    async function sendRoyaltyTransaction() {
        if (!tx) return;

        if (!window.ethereum) {
            status.textContent = "MetaMask tidak ditemukan.";

            setTriggerValue("royalty_tx_error", {
                message: "MetaMask tidak ditemukan."
            });

            return;
        }

        button.disabled = true;
        status.textContent =
            "Memeriksa akun dan jaringan MetaMask...";

        try {
            const accounts = await window.ethereum.request({
                method: "eth_requestAccounts"
            });

            const chainId = await window.ethereum.request({
                method: "eth_chainId"
            });

            if (!accounts || accounts.length === 0) {
                throw new Error(
                    "Hubungkan akun MetaMask terlebih dahulu."
                );
            }

            if (
                accounts[0].toLowerCase() !==
                tx.from.toLowerCase()
            ) {
                throw new Error(
                    "Pilih akun Platform Musik di MetaMask."
                );
            }

            if (parseInt(chainId, 16) !== Number(tx.chainId)) {
                throw new Error(
                    "Pilih jaringan Hardhat Local (Chain ID 31337)."
                );
            }

            status.textContent =
                "Menunggu konfirmasi transaksi di MetaMask...";

            const txHash = await window.ethereum.request({
                method: "eth_sendTransaction",
                params: [{
                    from: tx.from,
                    to: tx.to,
                    data: tx.data
                }]
            });

            status.textContent =
                "Transaksi dikirim: " + txHash;

            if (mounted) {
                setTriggerValue("royalty_tx_submitted", {
                    txHash: txHash,
                    requestId: tx.requestId
                });
            }

        } catch (error) {
            status.textContent =
                "Transaksi gagal: " + error.message;

            if (mounted) {
                setTriggerValue("royalty_tx_error", {
                    message: error.message
                });
            }

            button.disabled = false;
        }
    }

    button.addEventListener(
        "click",
        sendRoyaltyTransaction
    );

    return () => {
        mounted = false;

        button.removeEventListener(
            "click",
            sendRoyaltyTransaction
        );
    };
}
"""

royalty_tx_component = components.component(
    name="musicroyalty_royalty_transaction",
    html=ROYALTY_TX_HTML,
    css=ROYALTY_TX_CSS,
    js=ROYALTY_TX_JS,
)


# =========================================================
# KOMPONEN TRANSAKSI PAY ROYALTY
# =========================================================

PAY_TX_HTML = """
<div>
    <button id="pay-btn" type="button" disabled>
        Menunggu data transaksi...
    </button>

    <p id="pay-status">
        Siapkan transaksi pembayaran terlebih dahulu.
    </p>
</div>
"""


PAY_TX_CSS = """
#pay-btn {
    padding: 0.7rem 1rem;
    border: none;
    border-radius: 8px;
    background: #16a34a;
    color: white;
    font-weight: 600;
    cursor: pointer;
}

#pay-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

#pay-status {
    color: var(--st-text-color);
    overflow-wrap: anywhere;
}
"""


PAY_TX_JS = """
export default function(component) {
    const { parentElement, data, setTriggerValue } = component;

    const button = parentElement.querySelector("#pay-btn");
    const status = parentElement.querySelector("#pay-status");

    let mounted = true;

    // Pastikan elemen HTML tersedia
    if (!button || !status) {
        console.error("Elemen Pay Royalty tidak ditemukan.");
        return;
    }

    const tx = data && data.transaction
        ? data.transaction
        : null;

    // Periksa data transaksi
    if (tx && tx.to && tx.data && tx.from && tx.value) {
        button.disabled = false;
        button.textContent = "Konfirmasi Pay Royalty melalui MetaMask";
        status.textContent = "Transaksi siap dikirim.";
    } else {
        button.disabled = true;
        button.textContent = "Menunggu data transaksi...";
        status.textContent = "Siapkan transaksi terlebih dahulu.";
    }

    async function sendTransaction() {
        if (!tx) return;

        if (!window.ethereum) {
            setTriggerValue("pay_tx_error", {
                message: "MetaMask tidak ditemukan."
            });
            return;
        }

        button.disabled = true;
        status.textContent = "Memeriksa akun MetaMask...";

        try {
            const accounts = await window.ethereum.request({
                method: "eth_requestAccounts"
            });

            const chainId = await window.ethereum.request({
                method: "eth_chainId"
            });

            if (!accounts || accounts.length === 0) {
                throw new Error("Hubungkan MetaMask terlebih dahulu.");
            }

            if (
                accounts[0].toLowerCase() !==
                tx.from.toLowerCase()
            ) {
                throw new Error(
                    "Pilih akun Platform Musik di MetaMask."
                );
            }

            if (parseInt(chainId, 16) !== Number(tx.chainId)) {
                throw new Error(
                    "Pilih jaringan Hardhat Local (Chain ID 31337)."
                );
            }

            status.textContent = "Menunggu konfirmasi MetaMask...";

            const txHash = await window.ethereum.request({
                method: "eth_sendTransaction",
                params: [{
                    from: tx.from,
                    to: tx.to,
                    data: tx.data,
                    value: tx.value
                }]
            });

            status.textContent = "Transaksi dikirim: " + txHash;

            if (mounted) {
                setTriggerValue("pay_tx_submitted", {
                    txHash: txHash
                });
            }

        } catch (error) {
            status.textContent = "Transaksi gagal: " + error.message;

            if (mounted) {
                setTriggerValue("pay_tx_error", {
                    message: error.message
                });
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


pay_tx_component = components.component(
    name="musicroyalty_pay_transaction",
    html=PAY_TX_HTML,
    css=PAY_TX_CSS,
    js=PAY_TX_JS,
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
# 6. CREATE MUSIC BATCH
# =========================================================

st.divider()
st.subheader("3. Create Music Batch")
st.write("Buat batch musik baru melalui MetaMask. Fitur ini hanya dapat dijalankan oleh akun kreator.")

if "pending_create_batch_tx" not in st.session_state:
    st.session_state["pending_create_batch_tx"] = None
if "create_batch_request_id" not in st.session_state:
    st.session_state["create_batch_request_id"] = 0

with st.form("create_music_batch_form"):
    music_title = st.text_input("Judul Musik", placeholder="Contoh: Senja di Cirebon")
    transaction_type = st.text_input("Jenis Transaksi", placeholder="Contoh: Streaming")
    prepare_batch = st.form_submit_button("Siapkan Transaksi")

if prepare_batch:
    if not contract_ready:
        st.error("Smart Contract belum terhubung.")
    elif not wallet_connected:
        st.error("Hubungkan MetaMask terlebih dahulu.")
    elif not music_title.strip() or not transaction_type.strip():
        st.warning("Judul musik dan jenis transaksi wajib diisi.")
    else:
        try:
            wallet_chain_id = int(wallet["chainId"], 16)
            if wallet_chain_id != w3.eth.chain_id:
                raise ValueError("Pilih jaringan Hardhat Local di MetaMask.")

            creator_address = Web3.to_checksum_address(
                contract.functions.kreator().call()
            )
            if address.lower() != creator_address.lower():
                raise ValueError(
                    "Akun yang terhubung bukan akun kreator. Gunakan Hardhat Account #0."
                )

            calldata = contract.functions.createBatch(
                music_title.strip(),
                transaction_type.strip(),
            )._encode_transaction_data()

            st.session_state["create_batch_request_id"] += 1
            st.session_state["pending_create_batch_tx"] = {
                "from": address,
                "to": Web3.to_checksum_address(CONTRACT_ADDRESS),
                "data": calldata,
                "chainId": w3.eth.chain_id,
                "requestId": st.session_state["create_batch_request_id"],
            }
            st.success("Transaksi siap. Klik tombol MetaMask di bawah untuk melanjutkan.")
        except Exception as error:
            st.error("Tidak dapat menyiapkan transaksi.")
            st.code(str(error))

pending_tx = st.session_state.get("pending_create_batch_tx")
tx_result = tx_component(
    key="musicroyalty_create_batch_transaction",
    data={"transaction": pending_tx},
    default={"tx_submitted": None, "tx_error": None},
    on_tx_submitted_change=lambda: None,
    on_tx_error_change=lambda: None,
)

submitted = tx_result.get("tx_submitted")
tx_error = tx_result.get("tx_error")

if submitted and submitted.get("txHash"):
    tx_hash = submitted["txHash"]
    st.session_state["pending_create_batch_tx"] = None
    try:
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        if receipt.status == 1:
            st.success("Music Batch berhasil dibuat di blockchain!")
            st.write("Transaction Hash:")
            st.code(tx_hash)
            st.write("Block Number:", receipt.blockNumber)
            st.info("Cari batch menggunakan ID yang dihasilkan kontrak, misalnya MUSIC-1.")
        else:
            st.error("Transaksi tercatat tetapi gagal dijalankan oleh smart contract.")
            st.code(tx_hash)
    except Exception as error:
        st.warning("Transaksi sudah dikirim, tetapi receipt belum berhasil dibaca.")
        st.code(tx_hash)
        st.caption(str(error))

if tx_error:
    st.session_state["pending_create_batch_tx"] = None
    st.error(tx_error.get("message", "Transaksi gagal."))


# =========================================================
# 7. RECORD MUSIC USAGE
# =========================================================

st.divider()
st.subheader("Record Music Usage")

st.write(
    "Catat penggunaan musik berdasarkan Music Batch "
    "yang sudah dibuat."
)

with st.form("record_music_usage_form"):

    usage_batch_id = st.text_input(
        "Music Batch ID",
        placeholder="Contoh: MUSIC-1",
    )

    jenis_penggunaan = st.text_input(
        "Jenis Penggunaan Musik",
        placeholder="Contoh: Streaming",
    )

    submit_usage = st.form_submit_button(
        "Catat Penggunaan Musik"
    )

if submit_usage:

    if not contract_ready:
        st.error("Smart Contract belum terhubung.")

    elif not wallet_connected:
        st.error("Hubungkan MetaMask terlebih dahulu.")

    elif not usage_batch_id.strip():
        st.warning("Batch ID wajib diisi.")

    elif not jenis_penggunaan.strip():
        st.warning("Jenis penggunaan wajib diisi.")

    else:
        try:
            tx_hash = contract.functions.recordMusicUsage(
                usage_batch_id.strip(),
                jenis_penggunaan.strip()
            ).transact({
                "from": address
            })

            receipt = w3.eth.wait_for_transaction_receipt(
                tx_hash
            )

            if receipt.status == 1:
                st.success(
                    "Penggunaan musik berhasil dicatat!"
                )

                st.write(
                    "Transaction Hash:",
                    receipt.transactionHash.hex()
                )

                st.write("Status: USED")

            else:
                st.error("Transaksi gagal.")

        except Exception as error:
            st.error(
                "Gagal mencatat penggunaan musik."
            )
            st.code(str(error))

# =========================================================
# 8. ROYALTY DISTRIBUTION
# =========================================================

st.divider()
st.subheader("5. Royalty Distribution")

st.write(
    "Hitung dan distribusikan royalti musik melalui akun Platform Musik."
)

if "pending_royalty_tx" not in st.session_state:
    st.session_state["pending_royalty_tx"] = None

if "royalty_request_id" not in st.session_state:
    st.session_state["royalty_request_id"] = 0

with st.form("royalty_distribution_form"):

    royalty_batch_id = st.text_input(
        "Music Batch ID",
        placeholder="Contoh: MUSIC-1",
    )

    total_royalti_input = st.text_input(
        "Total Royalti (ETH)",
        placeholder="Contoh: 0.1",
    )

    prepare_royalty = st.form_submit_button(
        "Siapkan Transaksi Royalty Distribution"
    )


if prepare_royalty:

    if not contract_ready:
        st.error("Smart Contract belum terhubung.")

    elif not wallet_connected:
        st.error("Hubungkan MetaMask terlebih dahulu.")

    elif not royalty_batch_id.strip():
        st.warning("Batch ID wajib diisi.")

    elif not total_royalti_input.strip():
        st.warning("Total royalti wajib diisi.")

    else:
        try:
            from decimal import Decimal, InvalidOperation

            wallet_chain_id = int(wallet["chainId"], 16)

            if wallet_chain_id != w3.eth.chain_id:
                raise ValueError(
                    "Pilih jaringan Hardhat Local di MetaMask."
                )

            # Memeriksa apakah wallet merupakan Platform Musik
            platform_getter_exists = any(
                item.get("type") == "function"
                and item.get("name") == "platformMusik"
                for item in ABI
            )

            if platform_getter_exists:
                platform_address = Web3.to_checksum_address(
                    contract.functions.platformMusik().call()
                )

                if address.lower() != platform_address.lower():
                    raise ValueError(
                        "Wallet bukan akun Platform Musik. "
                        f"Gunakan alamat: {platform_address}"
                    )

            # Mengubah input ETH menjadi Wei
            total_royalti_eth = Decimal(
                total_royalti_input.strip()
            )

            if total_royalti_eth <= 0:
                raise ValueError(
                    "Total royalti harus lebih dari 0."
                )

            total_royalti_wei = w3.to_wei(
                total_royalti_eth,
                "ether",
            )

            # Menyiapkan calldata smart contract
            calldata = contract.functions.distributeRoyalty(
                royalty_batch_id.strip(),
                total_royalti_wei,
            )._encode_transaction_data()

            st.session_state["royalty_request_id"] += 1

            st.session_state["pending_royalty_tx"] = {
                "from": address,
                "to": Web3.to_checksum_address(CONTRACT_ADDRESS),
                "data": calldata,
                "chainId": w3.eth.chain_id,
                "requestId": st.session_state["royalty_request_id"],
            }

            st.success(
                "Transaksi siap. Klik tombol MetaMask di bawah."
            )

            st.write(
                "Total Royalti:",
                f"{total_royalti_eth} ETH",
            )

            st.write(
                "Total dalam Wei:",
                total_royalti_wei,
            )

        except Exception as error:
            st.error(
                "Tidak dapat menyiapkan transaksi Royalty Distribution."
            )
            st.code(str(error))


# Menampilkan tombol konfirmasi MetaMask
pending_royalty_tx = st.session_state.get(
    "pending_royalty_tx"
)

royalty_tx_result = royalty_tx_component(
    key="musicroyalty_royalty_transaction",
    data={"transaction": pending_royalty_tx},
    default={
        "royalty_tx_submitted": None,
        "royalty_tx_error": None,
    },
    on_royalty_tx_submitted_change=lambda: None,
    on_royalty_tx_error_change=lambda: None,
)

royalty_submitted = royalty_tx_result.get(
    "royalty_tx_submitted"
)

royalty_error = royalty_tx_result.get(
    "royalty_tx_error"
)


# Memeriksa hasil transaksi
if royalty_submitted and royalty_submitted.get("txHash"):

    royalty_tx_hash = royalty_submitted["txHash"]

    st.session_state["pending_royalty_tx"] = None

    try:
        receipt = w3.eth.wait_for_transaction_receipt(
            royalty_tx_hash,
            timeout=120,
        )

        if receipt.status == 1:

            st.success(
                "Royalty berhasil dihitung dan didistribusikan!"
            )

            st.write("Transaction Hash:")
            st.code(royalty_tx_hash)

            st.write("Block Number:", receipt.blockNumber)

            st.info(
                "Status batch sekarang seharusnya DISTRIBUTED."
            )

            st.write("Pembagian royalti berdasarkan smart contract:")

            col1, col2, col3, col4 = st.columns(4)

            col1.metric("Kreator", "60%")
            col2.metric("Produser", "20%")
            col3.metric("Penulis Lagu", "15%")
            col4.metric("Platform Musik", "5%")

            st.session_state["selected_batch"] = (
                royalty_batch_id.strip()
            )

        else:
            st.error(
                "Transaksi tercatat tetapi gagal dijalankan smart contract."
            )
            st.code(royalty_tx_hash)

    except Exception as error:
        st.warning(
            "Transaksi sudah dikirim, tetapi receipt belum berhasil dibaca."
        )
        st.code(royalty_tx_hash)
        st.caption(str(error))


if royalty_error:
    st.session_state["pending_royalty_tx"] = None

    st.error(
        royalty_error.get(
            "message",
            "Transaksi Royalty Distribution gagal.",
        )
    )


# =========================================================
# 9.PAY ROYALTY
# =========================================================

st.subheader("💸 Pay Royalty")

st.write(
    "Kirim pembayaran royalti kepada seluruh peserta "
    "berdasarkan hasil Royalty Distribution."
)

with st.form("pay_royalty_form"):
    pay_batch_id = st.text_input(
        "Batch ID",
        placeholder="Contoh: MUSIC-1"
    )

    pay_amount = st.text_input(
        "Total Pembayaran (ETH)",
        placeholder="Contoh: 0.1"
    )

    prepare_payment = st.form_submit_button(
        "Siapkan Pembayaran"
    )

if prepare_payment:
    try:
        from decimal import Decimal

        if not contract_ready:
            st.error("Smart contract belum terhubung.")

        elif not wallet_connected:
            st.error("Hubungkan MetaMask terlebih dahulu.")

        elif not pay_batch_id.strip() or not pay_amount.strip():
            st.error("Batch ID dan nominal wajib diisi.")

        else:
            # Pastikan akun yang digunakan adalah Platform Musik
            platform_address = contract.functions.platformMusik().call()

            if address.lower() != platform_address.lower():
                st.error("Gunakan akun Platform Musik di MetaMask.")

            else:
                # Konversi ETH menjadi Wei
                amount_wei = w3.to_wei(
                    Decimal(pay_amount.strip()),
                    "ether"
                )

                if amount_wei <= 0:
                    st.error("Nominal harus lebih dari 0 ETH.")

                else:
                    # Siapkan calldata fungsi payRoyalty
                    calldata = contract.functions.payRoyalty(
                        pay_batch_id.strip()
                    )._encode_transaction_data()

                    # Simpan data transaksi
                    st.session_state["pending_pay_batch_id"] = (
                        pay_batch_id.strip()
                    )

                    st.session_state["pending_pay_tx"] = {
                        "from": address,
                        "to": CONTRACT_ADDRESS,
                        "data": calldata,
                        "value": hex(amount_wei),
                        "chainId": wallet["chainId"]
                    }

                    st.success("Transaksi siap dikonfirmasi.")

    except Exception as e:
        st.error(f"Gagal menyiapkan pembayaran: {e}")


pending_pay_tx = st.session_state.get("pending_pay_tx")

if pending_pay_tx:
    pay_result = pay_tx_component(
        data={"transaction": pending_pay_tx},
        key="pay_royalty_transaction",
        on_pay_tx_submitted_change=lambda: None,
        on_pay_tx_error_change=lambda: None,
    )

    if pay_result.get("pay_tx_error"):
        st.error(
            pay_result["pay_tx_error"].get(
                "message", "Transaksi gagal."
            )
        )
        st.session_state["pending_pay_tx"] = None

    elif pay_result.get("pay_tx_submitted"):
        try:
            tx_hash = pay_result["pay_tx_submitted"]

            receipt = w3.eth.wait_for_transaction_receipt(
                tx_hash,
                timeout=120
            )

            if receipt.status == 1:
                st.success("Pembayaran royalti berhasil!")

                st.write("Transaction Hash:")
                st.code(tx_hash.hex())

                st.info(
                    "Status batch sekarang seharusnya COMPLETED."
                )

                st.session_state["selected_batch"] = (
                    st.session_state["pending_pay_batch_id"]
                )

            else:
                st.error("Transaksi gagal dieksekusi.")

            st.session_state["pending_pay_tx"] = None

        except Exception as e:
            st.error(f"Gagal memproses receipt: {e}")


# =========================================================
# 10. MUSIC BATCH
# =========================================================

st.divider()
st.subheader("4. Music Batch")

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

            st.table({
                "Informasi": list(music_data.keys()),
                "Nilai": list(music_data.values()),
            })

            st.session_state["selected_batch"] = batch_id.strip()

        except Exception as error:
            st.error("Gagal membaca Music Batch.")
            st.code(str(error))


# =========================================================
# 10. TRANSACTION HISTORY
# =========================================================

st.divider()
st.subheader("6. Transaction History")

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
# 11. MUSIC ROYALTY FEATURES
# =========================================================

st.divider()
st.subheader("7. Music Royalty Management")

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
# 12. FOOTER
# =========================================================

st.divider()

st.caption(
    "MusicRoyalty | Hardhat | MetaMask | Streamlit | Web3.py"
)
