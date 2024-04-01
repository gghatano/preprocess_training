import streamlit as st
import pandas as pd
import io
import os
import toml
import traceback

ss = st.session_state

# 状態変数==================================

if 'now' not in ss:  # 初期化
    ss.now = 0  # 初期化
    ss.user_code = None  # user_codeの初期化
    ss.problem_id = None  # 問題IDの初期化
    ss.validation_results = None  # バリデーション結果の初期化
    ss.is_submitted = False  # 提出状態の初期化
    ss.result_data = None  # 加工結果の初期化
    ss.error_message = None  # エラーメッセージの初期化

def countup():  # コールバック関数(1/3):次へ
    ss.now += 1

def countdown():  # コールバック関数(2/3):戻る
    ss.now -= 1

def reset():  # コールバック関数(3/3):リセット
    ss.now = 0
    ss.user_code = None  # user_codeのリセット
    ss.validation_results = None  # バリデーション結果のリセット
    ss.is_submitted = False  # 提出状態のリセット
    ss.result_data = None  # 加工結果のリセット
    ss.error_message = None  # エラーメッセージのリセット

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
def upload_and_validate(raw_data):
    uploaded_code = st.file_uploader("回答のPythonファイルをアップロードしてください", type=["py"])
    
    if uploaded_code is not None:
        code = uploaded_code.read().decode("utf-8")
        st.session_state.user_code = code
    else:
        code = st.session_state.user_code
    
    st.write("### Pythonコードを編集")
    code_area = st.empty()
    code = code_area.text_area("Pythonコードを編集してください", value=code or '''
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
''', height=400)
    
    if st.button("提出"):
        validation_results = []
        
        if "preprocess" in code:
            validation_results.append(("preprocess関数の実装", "OK"))
        else:
            validation_results.append(("preprocess関数の実装", "NG"))
        
        if 'if __name__ == "__main__":' in code:
            validation_results.append(("main関数の変更なし", "OK"))
        else:
            validation_results.append(("main関数の変更なし", "NG"))
        
        ss.validation_results = validation_results  # バリデーション結果をセッションステートに保存
        ss.error_message = None  # エラーメッセージをリセット
        
        if all(result[1] == "OK" for result in validation_results):
            ss.user_code = code  # user_codeをセッションステートに保存
            ss.is_submitted = True  # 提出状態をTrueに設定
            
            # プログラムで加工した結果を保存
            try:
                with open("answer.py", "w") as f:
                    f.write(code)
                answer_module = __import__("answer")
                result_data = answer_module.preprocess(raw_data.copy())  # raw_dataのコピーを使用
                ss.result_data = result_data  # 加工結果をセッションステートに保存
            except Exception as e:
                ss.error_message = traceback.format_exc()  # エラーメッセージを保存
    
    return ss.user_code

# 加工結果の比較と評価結果の表示
def compare_results(raw_data, processed_data, user_code):
    if user_code is None:
        st.write("## 結果")
        st.write("Pythonファイルがアップロードされていません。")
    else:
        with open("answer.py", "w") as f:
            f.write(user_code)
        try:
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
        except Exception as e:
            st.error("エラーが発生しました。")
            st.write("### エラーメッセージ")
            st.write(traceback.format_exc())

# トップページ
def show_top_page():
    st.title("前処理プログラム作成の練習アプリ")

    st.header("利用者向け")
    st.write("このアプリでは、データの前処理プログラムを作成する練習ができます。")
    st.write("1. サイドバーから問題を選択してください。")
    st.write("2. 問題の説明と変換前後のデータを確認してください。")
    st.write("3. サンプルPythonファイルをダウンロードし、前処理プログラムを作成してください。")
    st.write("4. 作成したPythonファイルをアップロードし、提出してください。")
    st.write("5. 結果を確認し、正解するまで試行錯誤してください。")
    st.write("バグの報告は、https://github.com/gghatano/preprocess_training のISSUEに立ててください。")

    st.header("開発者向け")
    st.write("このアプリのプログラムは、https://github.com/gghatano/preprocess_training にて管理しています。")
    st.write("問題を追加したい場合は、以下の手順に従ってください。")
    st.write("1. `problem****`フォルダを作成し、`toml`、`before.csv`、`after.csv`ファイルを追加してください。")
    st.write("2. プルリクエストを送信してください。")

# アプリ本体=================================

problems = load_problems()

st.sidebar.title("問題一覧")
problem_names = {folder: problem['name'] for folder, problem in problems.items()}
sorted_problems = sorted(problem_names.items(), key=lambda x: x[0])
selected_problem = st.sidebar.radio("問題を選択してください", ["トップページ"] + [f"{problem_id}: {problem_name}" for problem_id, problem_name in sorted_problems], format_func=lambda x: x.split(": ")[1] if ": " in x else x)

if selected_problem == "トップページ":
    show_top_page()
else:
    ss.problem_id = selected_problem.split(": ")[0]
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
        raw_data = pd.read_csv(os.path.join(ss.problem_id, "before.csv"))
        upload_and_validate(raw_data)
        
        if 'validation_results' in ss:
            st.write("### バリデーション結果")
            st.table(ss.validation_results)
        
        if 'error_message' in ss and ss.error_message is not None:
            st.error("エラーが発生しました。")
            st.write("### エラーメッセージ")
            st.write(ss.error_message)
        
        if 'result_data' in ss:
            col1, col2 = st.columns(2)
            with col1:
                st.write("### before.csv")
                st.write(raw_data)
            with col2:
                st.write("### 加工結果")
                st.write(ss.result_data)
        
        col1, col2, col3 = st.columns(3)
        if col1.button('前に戻る', key=f"{ss.problem_id}_prev_1"):
            countdown()
        col2.button('はじめから', key=f"{ss.problem_id}_reset_1", on_click=reset)
        if col3.button('次に進む', key=f"{ss.problem_id}_next_1"):
            if ss.is_submitted:  # 提出済みの場合のみStep3に遷移
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
