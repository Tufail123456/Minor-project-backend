import random
import pandas as pd
import os

class SimpleScalarFE:
    def __init__(self):
        self.s = random.randint(2, 20)   # Master Secret Key
        self.p = 1000003                 # Large prime modulus
        self.k = 7                       # Constant function f(x) = 7x

    def encrypt(self, x):
        r = random.randint(2, 20)
        c1 = (x + r * self.s) % self.p
        c2 = r
        return (c1, c2)

    def keygen(self):
        return (self.s * self.k) % self.p

    def evaluate(self, cipher, key):
        c1, c2 = cipher
        return (c1 * self.k - c2 * key) % self.p


# ---------------- SECRET SHARING ---------------- #

def generate_shares(y, num_parties=4):
    shares = []

    for _ in range(num_parties - 1):
        share = random.randint(-1000, 1000)
        shares.append(share)

    last_share = y - sum(shares)
    shares.append(last_share)

    return shares


# ---------------- MAIN PIPELINE ---------------- #

def process_input_and_store(x, file_name="fe_database.xlsx"):
    fe = SimpleScalarFE()

    # FE Steps
    cipher = fe.encrypt(x)
    key = fe.keygen()
    y = fe.evaluate(cipher, key)   # y = 7x

    # Secret Sharing
    shares = generate_shares(y, 4)

    assert sum(shares) == y, "Error in share generation!"

    # ---------------- STORE EVERYTHING ---------------- #

    data = {
        "Input (x)": [x],
        "Function": [f"f(x) = {fe.k}x"],
        "Multiplier (k)": [fe.k],
        "Ciphertext c1": [cipher[0]],
        "Ciphertext c2": [cipher[1]],
        "Random r": [cipher[1]],
        "Master Secret Key (s)": [fe.s],
        "Functional Key (SK)": [key],
        "Functional Output y = f(x)": [y],
        "Party 1 Share": [shares[0]],
        "Party 2 Share": [shares[1]],
        "Party 3 Share": [shares[2]],
        "Party 4 Share": [shares[3]]
    }

    df_new = pd.DataFrame(data)

    # Append if file exists
    if os.path.exists(file_name):
        df_existing = pd.read_excel(file_name)
        df_final = pd.concat([df_existing, df_new], ignore_index=True)
    else:
        df_final = df_new

    df_final.to_excel(file_name, index=False)

    print("✅ Data stored in fe_database.xlsx")


# ---------------- DRIVER CODE ---------------- #

if __name__ == "__main__":
    x = int(input("Enter your data: "))
    process_input_and_store(x)
