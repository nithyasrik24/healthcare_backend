from web3 import Web3
import json

# ===============================
# CONNECT TO GANACHE
# ===============================

GANACHE_URL = "http://127.0.0.1:7545"
web3 = Web3(Web3.HTTPProvider(GANACHE_URL))

# Check blockchain connection
if not web3.is_connected():
   print("Blockchain skipped")

print("Connected to Ganache")

# ===============================
# CONTRACT ADDRESS
# ===============================

contract_address = web3.to_checksum_address(
"0x7dE873612f77E2e5e6017f1f842C09543727e477"
)

# ===============================
# CONTRACT ABI
# ===============================

contract_abi = json.loads("""
[
	{
		"inputs": [
			{"internalType": "string","name": "_patientId","type": "string"},
			{"internalType": "string","name": "_reportHash","type": "string"}
		],
		"name": "storeReport",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [
			{"internalType": "uint256","name": "index","type": "uint256"}
		],
		"name": "getReport",
		"outputs": [
			{"internalType": "string","name": "","type": "string"},
			{"internalType": "string","name": "","type": "string"},
			{"internalType": "uint256","name": "","type": "uint256"}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [{"internalType": "uint256","name": "","type": "uint256"}],
		"name": "reports",
		"outputs": [
			{"internalType": "string","name": "patientId","type": "string"},
			{"internalType": "string","name": "reportHash","type": "string"},
			{"internalType": "uint256","name": "timestamp","type": "uint256"}
		],
		"stateMutability": "view",
		"type": "function"
	}
]
""")

# ===============================
# CREATE CONTRACT INSTANCE
# ===============================

contract = web3.eth.contract(
    address=contract_address,
    abi=contract_abi
)

# ===============================
# GANACHE ACCOUNT
# ===============================

account = web3.eth.accounts[0]

# ===============================
# STORE REPORT HASH
# ===============================

def store_report_on_blockchain(patient_id, report_hash):

    try:

        tx = contract.functions.storeReport(
            patient_id,
            report_hash
        ).transact({
            "from": account
        })

        receipt = web3.eth.wait_for_transaction_receipt(tx)

        return receipt.transactionHash.hex()

    except Exception as e:

        print("Blockchain error:", e)
        return None