from web3 import Web3
import json
from flask import Flask, request, jsonify
import os

app = Flask(__name__)
# ===============================
# 🔗 CONNECT TO ALCHEMY
# ===============================

ALCHEMY_URL = "https://eth-sepolia.g.alchemy.com/v2/FPtBm2pHPmyB7BT5BVVYw"

web3 = Web3(Web3.HTTPProvider(ALCHEMY_URL))

if web3.is_connected():
    print("✅ Connected to Blockchain (Sepolia)")
else:
    print("❌ Blockchain not connected")
    exit()

# ===============================
# 📍 YOUR CONTRACT ADDRESS
# ===============================

contract_address = Web3.to_checksum_address(
    "0x6eB3126CB36Cdc11a6DDe9A55EE46bCeD65DEE0a"
)

# ===============================
# 📜 CONTRACT ABI
# ===============================

contract_abi = [
    {
        "inputs": [
            {"internalType": "string", "name": "_patientId", "type": "string"},
            {"internalType": "string", "name": "_reportHash", "type": "string"}
        ],
        "name": "storeReport",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "index", "type": "uint256"}
        ],
        "name": "getReport",
        "outputs": [
            {"internalType": "string", "type": "string"},
            {"internalType": "string", "type": "string"},
            {"internalType": "uint256", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

# ===============================
# 📦 CREATE CONTRACT INSTANCE
# ===============================

contract = web3.eth.contract(
    address=contract_address,
    abi=contract_abi
)

# ===============================
# 👤 WALLET DETAILS
# ===============================

account = "0x8ddc3c78d6Bf9A42d0c923f58206373EC2E9caf5"
private_key = "3a888a22640aae84967d950eb12c347c09d5e8223af900d752542c72821b901b"

# ===============================
# 📝 STORE REPORT FUNCTION
# ===============================

def store_report(patient_id, report_hash):
    try:
        nonce = web3.eth.get_transaction_count(account)

        txn = contract.functions.storeReport(
            patient_id,
            report_hash
        ).build_transaction({
            'from': account,
            'nonce': nonce,
            'gas': 2000000,
            'gasPrice': web3.to_wei('10', 'gwei')
        })

        signed_txn = web3.eth.account.sign_transaction(txn, private_key)

        tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)

        print("⏳ Transaction sent:", web3.to_hex(tx_hash))

        receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

        print("✅ Transaction confirmed!")
        return receipt.transactionHash.hex()

    except Exception as e:
        print("❌ Error:", e)
        return None

# ===============================
# 📖 GET REPORT FUNCTION
# ===============================

def get_report(index):
    try:
        report = contract.functions.getReport(index).call()

        return {
            "patientId": report[0],
            "reportHash": report[1],
            "timestamp": report[2]
        }

    except Exception as e:
        print("❌ Error:", e)
        return None


@app.route('/store', methods=['POST'])
def store_api():
    data = request.json

    patient_id = data['patientId']
    report_hash = data['reportHash']

    tx = store_report(patient_id, report_hash)

    if tx:
        return jsonify({"status": "success", "txHash":tx})
    else:
        return jsonify({"status": "error"}),500

@app.route('/get/<int:index>', methods=['GET'])
def get_api(index):
    data = get_report(index)
    return jsonify(data)

@app.route("/")
def home():
    return "Server is running"

if __name__ == "__main__":
    port = int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0", port=port)