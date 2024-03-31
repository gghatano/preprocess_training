import streamlit as st
import pandas as pd
import io
import os
import toml

ss = st.session_state

# 状態変数==================================

if 'now' not in ss:  # 初期化
    ss.now = 0  # 初期化
    ss.user_code = None  # user_codeの初期化
    ss.problem_id = None  # 問題IDの初期化

def countup():  # コールバック関数(1/3):次へ
    ss.now += 1

def countdown():  # コールバック関数(2/3):戻る
    ss.now -= 1

def reset():  # コールバック関数(3/3):リセット
    ss.now = 0
    ss.user_code = None  # user_codeのリセット

# 問題の読み込み
def load_problems():
    problems = {}
    for folder in os.listdir("."):
        if folder.startswith("problem"):
            with open(os.path.join(folder, "explain.toml"), "r") as f:
                problem = toml.load(f)
                problems[folder] = problem
    return problems

# 問題の表示とデータのダウンロード
def show_question(problem_id):
    with open(os.path.join(problem_id, "explain.toml"), "r") as f:
        problem = toml.load(f)
    
    raw_data = pd.read_csv(os.path.join(problem_id, "before.csv"))
    processed_data = pd.read_csv(os.path.join(problem_id, "after.csv"))

    st.write(problem['description'])
    
    col1, col2 = st.columns(2)
    with col1:
        st.write("### 変換前データ")
        st.write(raw_data)
    with col2:
        st.write("### 変換後データ")
        st.write(processed_data)
    
    # データのダウンロード
    raw_buffer = io.BytesIO()
    processed_buffer = io.BytesIO()
    raw_data.to_csv(raw_buffer, index=False)
    processed_data.to_csv(processed_buffer, index=False)
    col1, col2, col3 = st.columns(3)
    col1.download_button("変換前データをダウンロード", raw_buffer.getvalue(), "before.csv", "text/csv")
    col2.download_button("変換後データをダウンロード", processed_buffer.getvalue(), "after.csv", "text/csv")
    
    # サンプルPythonファイルのダウンロード
    sample_code = '''
import sys
import pandas as pd

def preprocess(df):
    # ここに加工処理を実装する
    return df

if __name__ == "__main__":
    input_file = sys.argv[1]
    df = pd.read_csv(input_file)
    processed_df = preprocess(df)
    processed_df.to_csv("after.csv", index=False)
'''
    col3.download_button("サンプルPythonファイルをダウンロード", sample_code, "answer.py", "text/plain")

# ソースコードのアップロードと、アップロードされた内容のバリデーション
def upload_and_validate():
    uploaded_code = st.file_uploader("回答のPythonファイルをアップロードしてください", type=["py"])
    
    if uploaded_code is not None:
        code = uploaded_code.read().decode("utf-8")
        st.code(code, language="python")
        
        validation_results = []
        
        if "preprocess" in code:
            validation_results.append(("preprocess関数の実装", "OK"))
        else:
            validation_results.append(("preprocess関数の実装", "NG"))
        
        if 'if __name__ == "__main__":' in code:
            validation_results.append(("main関数の変更なし", "OK"))
        else:
            validation_results.append(("main関数の変更なし", "NG"))
        
        st.write("### バリデーション結果")
        st.table(validation_results)
        
        if all(result[1] == "OK" for result in validation_results):
            ss.user_code = code  # user_codeをセッションステートに保存
    
    return ss.user_code

# 加工結果の比較と評価結果の表示
def compare_results(raw_data, processed_data, user_code):
    if user_code is None:
        st.write("## 結果")
        st.write("Pythonファイルがアップロードされていません。")
    else:
        with open("answer.py", "w") as f:
            f.write(user_code)
        answer_module = __import__("answer")
        result_data = answer_module.preprocess(raw_data)
        
        st.write("## 結果")
        if result_data.equals(processed_data):
            st.success("正解！")
        else:
            st.error("不正解！")
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("### 期待する結果")
            st.write(processed_data)
        with col2:
            st.write("### 実際の結果")
            st.write(result_data)

# アプリ本体=================================

problems = load_problems()

st.sidebar.title("問題一覧")
problem_names = {folder: problem['name'] for folder, problem in problems.items()}
selected_problem = st.sidebar.radio("問題を選択してください", list(problem_names.keys()), format_func=lambda x: problem_names[x])
ss.problem_id = selected_problem

st.title(problems[ss.problem_id]['name'])

if ss.now == 0:
    st.write('#### Step1: 問題の確認')
    show_question(ss.problem_id)
    
    col1, col2, col3 = st.columns(3)
    col1.button('前に戻る', key=f"{ss.problem_id}_prev_0", disabled=True)
    col2.button('はじめから', key=f"{ss.problem_id}_reset_0", on_click=reset)
    if col3.button('次に進む', key=f"{ss.problem_id}_next_0"):
        countup()
    
elif ss.now == 1:
    st.write('#### Step2: Pythonコードの提出')
    upload_and_validate()
    
    col1, col2, col3 = st.columns(3)
    if col1.button('前に戻る', key=f"{ss.problem_id}_prev_1"):
        countdown()
    col2.button('はじめから', key=f"{ss.problem_id}_reset_1", on_click=reset)
    if col3.button('次に進む', key=f"{ss.problem_id}_next_1"):
        countup()
    
elif ss.now == 2:
    st.write('#### Step3: 結果の確認')
    raw_data = pd.read_csv(os.path.join(ss.problem_id, "before.csv"))
    processed_data = pd.read_csv(os.path.join(ss.problem_id, "after.csv"))
    compare_results(raw_data, processed_data, ss.user_code)
    
    col1, col2, col3 = st.columns(3)
    if col1.button('前に戻る', key=f"{ss.problem_id}_prev_2"):
        countdown()
    col2.button('はじめから', key=f"{ss.problem_id}_reset_2", on_click=reset)
    col3.button('次に進む', key=f"{ss.problem_id}_next_2", disabled=True)
    
else:
    st.write('### 完了！')
    st.success('全てのステップが完了しました')
