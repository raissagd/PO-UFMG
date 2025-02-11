import numpy as np
from gurobipy import Model, GRB

class SupplyChainOptimization:
    def __init__(self):
        # Initialize an empty model and decision variables
        self.model = None
        self.xik = None  # Decision variables for flow from factories to CDs
        self.ykj = None  # Decision variables for flow from CDs to clients
    
    def build_model(self, num_factories, num_cds, num_clients, si, tk, dj, cik, ckj):
        # Create and name the optimization model
        self.model = Model("SupplyChainOptimization")

        # Save the input data as class attributes for later use
        self.num_factories = num_factories  # Number of factories
        self.num_cds = num_cds             # Number of consolidation/distribution centers (CDs)
        self.num_clients = num_clients     # Number of clients
        self.si = si  # Array of factory capacities
        self.tk = tk  # Array of CD capacities
        self.dj = dj  # Array of client demands
        self.cik = cik  # Cost of transporting goods from factories to CDs
        self.ckj = ckj  # Cost of transporting goods from CDs to clients

        # Add decision variables
        self.xik = self.model.addVars(
            num_factories, num_cds, vtype=GRB.INTEGER, name="xik"
        )  # Flow from factory `i` to CD `k`
        self.ykj = self.model.addVars(
            num_cds, num_clients, vtype=GRB.INTEGER, name="ykj"
        )  # Flow from CD `k` to client `j`

        # Define the objective function: minimize total transportation costs
        self.model.setObjective(
            sum(cik[i, k] * self.xik[i, k] for i in range(num_factories) for k in range(num_cds)) +
            sum(ckj[k, j] * self.ykj[k, j] for k in range(num_cds) for j in range(num_clients)),
            GRB.MINIMIZE
        )

        # Add constraints to ensure problem feasibility
        # (1) Client demands must be fully satisfied
        for j in range(num_clients):
            self.model.addConstr(
                sum(self.ykj[k, j] for k in range(num_cds)) == dj[j], name=f"Demand_{j}"
            )

        # (2) CD capacities must not be exceeded
        for k in range(num_cds):
            self.model.addConstr(
                sum(self.xik[i, k] for i in range(num_factories)) <= tk[k], name=f"CD_Capacity_{k}"
            )

        # (3) Factory production must not exceed factory capacities
        for i in range(num_factories):
            self.model.addConstr(
                sum(self.xik[i, k] for k in range(num_cds)) <= si[i], name=f"Factory_Capacity_{i}"
            )

        # (4) Flow conservation at CDs: inflow to a CD must equal outflow from the CD
        for k in range(num_cds):
            self.model.addConstr(
                sum(self.xik[i, k] for i in range(num_factories)) ==
                sum(self.ykj[k, j] for j in range(num_clients)), name=f"Flow_Conservation_{k}"
            )

    def solve(self, output_file="results.txt"):
        if not self.model:
                raise Exception("Model has not been built. Use `build_model` first.")

        # Solve the optimization problem
        self.model.optimize()

        # Write results to a file
        with open(output_file, "w") as file:
            # Write instance details
            file.write("Instance Details:\n")
            file.write(f"Number of factories: {self.num_factories}\n")
            file.write(f"Number of CDs: {self.num_cds}\n")
            file.write(f"Number of clients: {self.num_clients}\n\n")

            file.write("Factory capacities (si):\n")
            file.write(f"{self.si}\n\n")

            file.write("CD capacities (tk):\n")
            file.write(f"{self.tk}\n\n")

            file.write("Client demands (dj):\n")
            file.write(f"{self.dj}\n\n")

            file.write("Transport costs (factory -> CD) (cik):\n")
            file.write(f"{self.cik}\n\n")

            file.write("Transport costs (CD -> client) (ckj):\n")
            file.write(f"{self.ckj}\n\n")

            # Write optimization results
            if self.model.status == GRB.OPTIMAL:
                file.write("Optimal solution found:\n")
                file.write(f"Objective value: {self.model.objVal}\n\n")

                # Write performance details
                file.write(f"Gurobi iterations: {self.model.IterCount}\n")
                file.write(f"Gurobi runtime (seconds): {self.model.Runtime}\n")

                file.write("Factory -> CD flows (xik):\n")
                for i in range(self.num_factories):
                    for k in range(self.num_cds):
                        if self.xik[i, k].x > 0:
                            file.write(f"xik[{i},{k}] = {self.xik[i, k].x}\n")

                file.write("\nCD -> Client flows (ykj):\n")
                for k in range(self.num_cds):
                    for j in range(self.num_clients):
                        if self.ykj[k, j].x > 0:
                            file.write(f"ykj[{k},{j}] = {self.ykj[k, j].x}\n")
                print(f"Results saved to {output_file}")
            else:
                file.write("No optimal solution found.\n")
                print(f"No optimal solution found. See {output_file} for details.")