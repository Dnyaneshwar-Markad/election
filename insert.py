# import pandas as pd
# from sqlalchemy import create_engine

# # ----------------- CONFIG -----------------
# CSV_URL = "https://raw.githubusercontent.com/Dnyaneshwar-Markad/election_backend/refs/heads/main/ward_10_2.csv"
# TABLE_NAME = "VoterList"

# # Columns in CSV to ignore (auto-increment or default)
# COLUMNS_TO_INSERT = ['ACNo',	'PartNo',	'SectionNo',	'SINo',	'HouseNo',	'VHouseNo',	'EName'	,'VEName',	'Sex'	,'RName',	'VRName',	'RType',	'Age',	'IDCardNo',	'Address',	'VAddress',	'PSName',	'VPSName',	'Surname'
# ]

# # Neon DB connection string
# DB_CONNECTION_STRING = "postgresql://neondb_owner:npg_rs1bVogh7EtU@ep-weathered-math-a1pj9ocn-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
# # -----------------------------------------

# def main():
#     try:
#         # 1. Read CSV
#         print("Reading CSV...")
#         df = pd.read_csv(CSV_URL)

#         # 2. Keep only necessary columns
#         df = df[COLUMNS_TO_INSERT]

#         # 3. Create database connection
#         print("Connecting to Neon database...")
#         engine = create_engine(DB_CONNECTION_STRING)

#         # 4. Insert data into table
#         print(f"Inserting data into '{TABLE_NAME}'...")
#         df.to_sql(TABLE_NAME, engine, if_exists='append', index=False)

#         print("✅ CSV data inserted successfully!")

#     except Exception as e:
#         print("❌ Error:", e)

# if __name__ == "__main__":
#     main()

import pandas as pd
from sqlalchemy import create_engine, inspect

# ----------------- CONFIG -----------------
CSV_PATH = r"C:\Users\HP\OneDrive\Desktop\Ward_11.csv"
TABLE_NAME = "VoterList"

# Columns in CSV to ignore (auto-increment or default)
IGNORE_COLUMNS = ['Visited_2']

# Neon DB connection string
DB_CONNECTION_STRING = "postgresql://neondb_owner:npg_rs1bVogh7EtU@ep-weathered-math-a1pj9ocn-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
# -----------------------------------------

def main():
    try:
        # 1. Read CSV
        print("Reading CSV...")
        df = pd.read_csv(CSV_PATH)

        # 2. Drop ignored columns if they exist
        df = df.drop(columns=[col for col in IGNORE_COLUMNS if col in df.columns])

        # 3. Connect to Neon
        print("Connecting to Neon database...")
        engine = create_engine(DB_CONNECTION_STRING)

        # 4. Get actual columns in the table
        inspector = inspect(engine)
        table_columns = [col['name'] for col in inspector.get_columns(TABLE_NAME)]
        print("Columns in table:", table_columns)

        # 5. Keep only columns that exist in table
        columns_to_insert = [col for col in df.columns if col in table_columns]
        skipped_columns = [col for col in df.columns if col not in table_columns]
        if skipped_columns:
            print("Skipped columns (not in table):", skipped_columns)

        df_to_insert = df[columns_to_insert]

        # 6. Insert data
        print(f"Inserting {len(df_to_insert)} rows with columns: {columns_to_insert}")
        df_to_insert.to_sql(TABLE_NAME, engine, if_exists='append', index=False)

        print("✅ CSV data inserted successfully!")

    except Exception as e:
        print("❌ Error:", e)

if __name__ == "__main__":
    main()
