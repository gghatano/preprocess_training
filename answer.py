
import sys
import pandas as pd

def preprocess(df):
    # ここに加工処理を実装する
hoge
    return df

if __name__ == "__main__":
    input_file = sys.argv[1]
    df = pd.read_csv(input_file)
    processed_df = preprocess(df)
    processed_df.to_csv("after.csv", index=False)
