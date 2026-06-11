import pandas as pd

class MPCParty:
    def __init__(self, party_id):
        self.party_id = party_id
        self.shares = []

    def load_shares(self, shares_column):
        self.shares = shares_column.tolist()

    def compute_local_sum(self):
        return sum(self.shares)


class MPCProtocol:
    def __init__(self, file_name="fe_database.xlsx", k=7):
        self.file_name = file_name
        self.k = k
        self.parties = []
        self.num_inputs = 0

    def load_data(self):
        df = pd.read_excel(self.file_name)

        # Number of inputs (rows)
        self.num_inputs = len(df)

        # Initialize 4 parties
        self.parties = [
            MPCParty(1),
            MPCParty(2),
            MPCParty(3),
            MPCParty(4)
        ]

        # Load shares into each party
        self.parties[0].load_shares(df["Party 1 Share"])
        self.parties[1].load_shares(df["Party 2 Share"])
        self.parties[2].load_shares(df["Party 3 Share"])
        self.parties[3].load_shares(df["Party 4 Share"])

    def compute_average(self):
        # Each party computes local sum
        local_sums = []
        for party in self.parties:
            local_sum = party.compute_local_sum()
            local_sums.append(local_sum)

        # Combine results (secure aggregation)
        total_sum_y = sum(local_sums)

        # Compute averages
        avg_y = total_sum_y / self.num_inputs
        avg_x = avg_y / self.k

        return avg_y, avg_x


# ---------------- DRIVER ---------------- #

if __name__ == "__main__":
    mpc = MPCProtocol("fe_database.xlsx", k=7)

    mpc.load_data()

    avg_y, avg_x = mpc.compute_average()

    print("✅ MPC Computation Complete")
    print(f"Average of encrypted outputs (avg_y): {avg_y}")
    print(f"Recovered Average of original inputs (avg_x): {avg_x}")
