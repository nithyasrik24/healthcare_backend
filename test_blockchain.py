from blockchain import store_hash

# Test hash value
test_value = "test_patient_data_123"

tx_id = store_hash(test_value)

print("Transaction successful!")
print("Transaction ID:", tx_id)