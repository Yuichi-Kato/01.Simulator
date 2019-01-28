# coding: utf-8
# UNION_prep_output0.5 2018/12/17
#0.3 エラーファイル複数カラム対応
#0.4 従来生産拠点のないREC抜き出す、処理件数をoutput
#0.5 設備管理単位コードを付与
#0.6 BMJP除去
#0.7 ランデットコスト、RBS_製造原価の計算式を修正,単価に*数量、エラー落ちした復活RECのインナーコード先頭2文字に'E'を入れる
#0.8 納区、UFでエラー落ちした復活RECはインナーコードの変更を行わない
#0.9 エラーファイル修正されたので、エラーファイルのヘッダー付与を削除
#    準備処理時エラーで落ちたRECにUF種別やJST時間、エラーコード,をACE参照スキーマに付与
#0.10 Global_Noをキーとして利用しない（Global_Noが意図せず重複してしまうこともあるため）、日本時間昇順に並べ替え
#0.11 ACE仕入先　FCNTをFCNXへ
#0.12 見積もりUF RECに従来生産拠点をつけない、中口になってしまい、スキーマと生産拠点が合わないREC除く、結果の出力内容を変更

# モジュールのインポート
import os, tkinter, tkinter.filedialog, tkinter.messagebox
import csv
import pandas as pd
import numpy as np


# from tqdm import tqdm
csv.field_size_limit(1000000000)

font = 'utf-8'
# font='shift_jisx0213'

#管理単位CD一覧読み込み
MNG_Unit = pd.read_csv('MNG_UNIT_20170101_20180930.csv', encoding=font, dtype='object', index_col=None)
MNG_header = MNG_Unit.columns.values

# ファイル名と変数名の記述
#file_name = ['準備処理インプット', 'default', 'default_error', 'MPA', 'MPA_error', '阿見', '阿見_error', 'FCN', 'FCN_error', 'SPC',
#             'SPC_error', '阿見_cost', '阿見_cost_error', 'FCN_cost', 'FCN_cost_error', 'SPC_cost', 'SPC_cost_error']
f_name = ['input.tsv', 'default.tsv', 'default_e.tsv', 'mpa.tsv', 'mpa_e.tsv', 'ami_p.tsv', 'ami_p_e.tsv', 'fcn_p.tsv',
          'fcn_p_e.tsv', 'spc_p.tsv', 'spc_p_e.tsv', 'ami_c.tsv', 'ami_c_e.tsv', 'fcn_c.tsv', 'fcn_c_e.tsv',
          'spc_c.tsv', 'spc_c_e.tsv']
# f_name=['準備処理インプット.tsv','default.tsv','default_error.tsv','MPA.tsv','MPA_error.tsv','阿見.tsv','阿見_error.tsv','FCN.tsv','FCN_error.tsv','SPC.tsv','SPC_error.tsv','阿見_cost.tsv','阿見_cost_error.tsv','FCN_cost.tsv','FCN_cost_error.tsv','SPC_cost.tsv','SPC_cost_error.tsv']
# f_name=[]
# f_pass=[]
file_list = []

# フォルダ選択ダイアログの表示
root = tkinter.Tk()
root.withdraw()
fTyp = [('', '*')]
iDir = os.path.abspath(os.path.dirname(__file__))
tkinter.messagebox.showinfo('準備処理アウトプットマージ', 'ディレクトリを選択してください！')

f_pass = tkinter.filedialog.askdirectory(initialdir=iDir)

# ファイル名固定
for f in range(0, len(f_name)):
    os.chdir(f_pass)
    file = pd.read_table(f_name[f], dtype='object', index_col=None)
    var_list = ['発注現法仕入値','ランデットコスト','RBS_製造原価', 'RBS_販管費', 'RBS_輸送費', 'RBS_関税', 'RBS_輸入諸掛', '発注現法実績売値' , 'RBS_マージン単価']
    file[var_list] = file[var_list].astype(float)
    file = file.astype({'数量': int})
    file = file.fillna({'RBS_販管費': 0, 'RBS_輸送費': 0, 'RBS_関税': 0, 'RBS_輸入諸掛': 0, 'RBS_マージン単価': 0})
    file_list.append(file)

#データを保持
prep_input = file_list[0]
default = file_list[1]
default_e = file_list[2]
MPA = file_list[3]
MPA_e = file_list[4]
AMI_C = file_list[11]
AMI_P = file_list[5]
FCN_C = file_list[13]
FCN_P = file_list[7]
SPC_C = file_list[15]
SPC_P = file_list[9]
AMI_C_e = file_list[12]
AMI_P_e = file_list[6]
FCN_C_e = file_list[14]
FCN_P_e = file_list[8]
SPC_C_e = file_list[16]
SPC_P_e = file_list[10]

# エラーファイルを結合,重複削除
error_list = default_e
error_list = error_list.append(MPA_e, sort=False)
error_list = error_list.append(AMI_C_e, sort=False)
error_list = error_list.append(FCN_C_e, sort=False)
error_list = error_list.append(SPC_C_e, sort=False)
error_list = error_list.append(AMI_P_e, sort=False)
error_list = error_list.append(FCN_P_e, sort=False)
error_list = error_list.append(SPC_P_e, sort=False)

# 正常処理のファイルのエラーRECに対し処理
E_delete = [default, MPA, AMI_P, FCN_P, SPC_P, AMI_C, FCN_C, SPC_C]
for s in range (0, len(E_delete)):
    EE = E_delete[s]
    # エラーRECをエラーファイルに結合
    error_list = error_list.append(EE[EE['ACE参照スキーマ'].isnull()], sort = False)
    error_list = error_list.append(EE[EE['ACE仕入先コード'] == 'BMJP'], sort=False)
    # エラーREC（ACE参照スキーマがNull,仕入先がBMJP）を削除
    EE = EE.dropna(subset=['ACE参照スキーマ'])
    EE = EE[EE['ACE仕入先コード'] != 'BMJP']
    E_delete[s] = EE
# error_list重複削除
error_list.drop_duplicates(keep='first', inplace=True)

default = E_delete[0]
MPA = E_delete[1]
AMI_P = E_delete[2]
FCN_P = E_delete[3]
SPC_P = E_delete[4]
AMI_C = E_delete[5]
FCN_C = E_delete[6]
SPC_C = E_delete[7]

# 仕入値スキーマのRBS_製造原価（仕入先売値）を発注現法仕入値に転記
MPA['発注現法仕入値'] = MPA['RBS_製造原価']
# 製造原価(本当にRBS_製造原価に入れたい値) = (RBS_製造原価 - RBS_販管費 - RBS_マージン単価)
MPA['RBS_製造原価'] = MPA['RBS_製造原価'] - MPA['RBS_販管費'] - MPA['RBS_マージン単価']
# ランデットコスト=製造原価 + RBS_販管費 + RBS_関税 + RBS_輸入諸掛 + RBS_輸送費
MPA=MPA.assign(ランデットコスト=lambda MPA:MPA.RBS_製造原価 + MPA.RBS_販管費 + MPA.RBS_関税 + MPA.RBS_輸入諸掛 + MPA.RBS_輸送費)
# 各費目に数量をかける
MPA=MPA.assign(発注現法仕入値=lambda MPA:MPA.発注現法仕入値 * MPA.数量,
               ランデットコスト=lambda MPA:MPA.ランデットコスト * MPA.数量,
               発注現法実績売値=lambda MPA:MPA.発注現法実績売値 * MPA.数量,
               RBS_製造原価=lambda MPA:MPA.RBS_製造原価 * MPA.数量,
               RBS_マージン単価=lambda MPA:MPA.RBS_マージン単価 * MPA.数量,
               RBS_販管費=lambda MPA:MPA.RBS_販管費 * MPA.数量,
               RBS_輸送費=lambda MPA:MPA.RBS_輸送費 * MPA.数量,
               RBS_関税=lambda MPA:MPA.RBS_関税 * MPA.数量,
               RBS_輸入諸掛=lambda MPA:MPA.RBS_輸入諸掛 * MPA.数量)
MPA = MPA.round({'発注現法仕入値': 3,'ランデットコスト': 3,'RBS_製造原価': 3, 'RBS_販管費': 3, 'RBS_輸送費': 3, 'RBS_関税': 3, 'RBS_輸入諸掛': 3, '発注現法実績売値': 3, 'RBS_マージン単価': 3})

P_tbl = [AMI_P, FCN_P, SPC_P]
C_tbl = [AMI_C, FCN_C, SPC_C]

# 内製分だけ繰り返す
for s in range(0, len(P_tbl)):
    P = P_tbl[s]
    C = C_tbl[s]

    #R.B.S_製造原価（仕入先売値）を発注現法仕入先売値へコピー
    P=P.assign(発注現法仕入値=lambda P: P.RBS_製造原価)

    # 製造原価スキーマのRBS_製造原価のみ保持、名前の変更
    C = C.loc[::, ['番号', 'RBS_製造原価', 'RBS_販管費' , 'RBS_マージン単価']]
    C = C.rename(columns={'RBS_製造原価': 'RBS_製造原価_C' , 'RBS_販管費' : 'RBS_販管費_C', 'RBS_マージン単価' : 'RBS_マージン単価_C'})

    # 仕入値と製造原価スキーマ２つのテーブルをマージ、値の入れかえ
    # 仕入値スキーマのRBS_製造原価（仕入先売値）を発注現法仕入値に転記
    P['発注現法仕入値'] = P['RBS_製造原価']
    #P,Cのテーブルを結合
    P = pd.merge(P, C, on='番号', how='left')
    #製造原価(本当にRBS_製造原価に入れたい値) = (RBS_製造原価_C - RBS_販管費_C - RBS_マージン単価_C)
    P['RBS_製造原価'] = P['RBS_製造原価_C'] - P['RBS_販管費_C'] - P['RBS_マージン単価_C']
    # ランデットコストを算出　ランデットコスト=製造原価 + RBS_販管費 + RBS_関税 + RBS_輸入諸掛 + RBS_輸送費
    P['ランデットコスト'] = P['RBS_製造原価'] + P['RBS_販管費'] + P['RBS_輸送費'] + P['RBS_関税'] + P['RBS_輸入諸掛']

    # 単価をREC金額に変更
    P = P.assign(発注現法仕入値=lambda P: P.発注現法仕入値 * P.数量,
                 ランデットコスト=lambda P: P.ランデットコスト * P.数量,
                 発注現法実績売値=lambda P: P.発注現法実績売値 * P.数量,
                 RBS_製造原価=lambda P: P.RBS_製造原価 * P.数量,
                 RBS_マージン単価=lambda P: P.RBS_マージン単価 * P.数量,
                 RBS_販管費=lambda P: P.RBS_販管費 * P.数量,
                 RBS_輸送費=lambda P: P.RBS_輸送費 * P.数量,
                 RBS_関税=lambda P: P.RBS_関税 * P.数量,
                 RBS_輸入諸掛=lambda P: P.RBS_輸入諸掛 * P.数量)
    P.drop(['RBS_製造原価_C','RBS_販管費_C','RBS_マージン単価_C'], axis=1, inplace=True)
    P = P.round({'発注現法仕入値': 3,'ランデットコスト': 3,'RBS_製造原価': 3, 'RBS_販管費': 3, 'RBS_輸送費': 3, 'RBS_関税': 3, 'RBS_輸入諸掛': 3, '発注現法実績売値': 3, 'RBS_マージン単価': 3})

    P_tbl[s] = P
    C_tbl[s] = C

    P_sample=P

AMI_P = P_tbl[0]
FCN_P = P_tbl[1]
SPC_P = P_tbl[2]

# ４つのファイルを結合
check_input = MPA
check_input = check_input.append(AMI_P, sort=False)
check_input = check_input.append(FCN_P, sort=False)
check_input = check_input.append(SPC_P, sort=False)

#管理単位CD付与
check_input=pd.merge(check_input,MNG_Unit,left_on='商品コード', right_on='PRODUCT_CD',how='left')
#管理単位CD一覧がExcelの際は下記を使う
#check_input.loc[check_input['RBS_受注現法仕入先コード']=='7017','RBS_管理単位コード']=check_input[7017]
#check_input.loc[check_input['RBS_受注現法仕入先コード']=='3764','RBS_管理単位コード']=check_input[3764]
check_input.loc[check_input['RBS_受注現法仕入先コード']=='7017','RBS_管理単位コード']=check_input['7017']
check_input.loc[check_input['RBS_受注現法仕入先コード']=='3764','RBS_管理単位コード']=check_input['3764_ALL']
check_input.loc[check_input['RBS_受注現法仕入先コード']=='0FCN','RBS_管理単位コード']=check_input['0FCN_ALL']
check_input.loc[check_input['RBS_受注現法仕入先コード']=='SPCM','RBS_管理単位コード']=check_input['SPCM_ALL']
check_input.drop(MNG_header, axis=1, inplace=True)

# スキーマと生産拠点が一致していないRECはエラーファイルへ
# 一致していないRECは別だし
SUP_NG = check_input[~(((check_input['ACE参照スキーマ']=='MPA') & (check_input['RBS_受注現法仕入先コード']=='7017')) |
                      ((check_input['ACE参照スキーマ']=='AMI') & (check_input['RBS_受注現法仕入先コード']=='3764')) |
                      ((check_input['ACE参照スキーマ']=='CHN') & (check_input['RBS_受注現法仕入先コード']=='0FCN')) |
                      ((check_input['ACE参照スキーマ']=='SPCM') & (check_input['RBS_受注現法仕入先コード']=='SPCM')))]
# 一致してるファイルのみ、SUP_NGを生成してからcheck_inputを上書き
check_input = check_input[(((check_input['ACE参照スキーマ']=='MPA') & (check_input['RBS_受注現法仕入先コード']=='7017')) |
                      ((check_input['ACE参照スキーマ']=='AMI') & (check_input['RBS_受注現法仕入先コード']=='3764')) |
                      ((check_input['ACE参照スキーマ']=='CHN') & (check_input['RBS_受注現法仕入先コード']=='0FCN')) |
                      ((check_input['ACE参照スキーマ']=='SPCM') & (check_input['RBS_受注現法仕入先コード']=='SPCM')))]

# 結合ファイルとdefaultファイルを比較し従来拠点にフラグを付ける
make_flg = check_input.append(default, sort=False)
df_make_flg = make_flg.duplicated(subset=['番号', 'RBS_受注現法仕入先コード'], keep=False)
make_flg.loc[df_make_flg, '従来生産拠点フラグ'] = 1

make_flg = make_flg[make_flg['ACE参照スキーマ'] != 'Default']

check_input = make_flg

# 正常処理したRECの件数
n_True=check_input['従来生産拠点フラグ'] == 1
num_True=n_True.sum()

#従来生産拠点がないREC件数の取得
n_jri_e = make_flg.loc[::,['番号', '従来生産拠点フラグ']]#番号と従来生産拠点フラグのみ
n_jri_e = n_jri_e.sort_values(['番号', '従来生産拠点フラグ'])
n_jri_e.drop_duplicates(subset=['番号'], keep='first', inplace=True)#重複削除
n_jri_e = n_jri_e[n_jri_e['従来生産拠点フラグ'].isnull()]#従来生産拠点がnullのみ残す
num_jri_e=len(n_jri_e)#件数数える

#従来生産拠点フラグがないものをcheck_inputから削除
check_input = pd.merge(check_input,n_jri_e,on='番号', how='left', indicator = True)
check_input = check_input[check_input['_merge'] == 'left_only']
check_input.drop(['_merge', '従来生産拠点フラグ_y'], axis=1, inplace=True)
check_input = check_input.rename(columns={'従来生産拠点フラグ_x': '従来生産拠点フラグ'})

# インプットファイルと結合し重複しないRECのインプットファイルのみ残す
prep_input_error = prep_input.append(check_input, sort=False)
prep_input_error.drop_duplicates(subset='番号', keep=False, inplace=True)
#インプットから復活させるRECの従来生産拠点フラグに１つける
prep_input_error['従来生産拠点フラグ'] = 1

# error_listから復活RECにACE_アンフィット区分とACE_エラーメッセージコードを付与
error_list_t = error_list.loc[::, ['番号', 'JST変換受注日・JST変換見積回答日','JST変換受注時間・JST変換見積回答時間','ACE_アンフィット区分', 'ACE_エラーメッセージコード' ]]
error_list_t = error_list_t.rename(columns={'JST変換受注日・JST変換見積回答日' : 'JST変換受注日・JST変換見積回答日_e','JST変換受注時間・JST変換見積回答時間' : 'JST変換受注時間・JST変換見積回答時間_e'})
# 一つのRECに各スキーマで複数のエラーが発生した際は上段にあるエラーを優先する
error_list_t.drop_duplicates(subset='番号', keep='first', inplace=True)
prep_input_error = pd.merge(prep_input_error, error_list_t, on='番号', how='left',indicator = True)
prep_input_error.loc[prep_input_error['_merge'] == 'both','JST変換受注日・JST変換見積回答日'] = prep_input_error['JST変換受注日・JST変換見積回答日_e']
prep_input_error.loc[prep_input_error['_merge'] == 'both','JST変換受注時間・JST変換見積回答時間'] = prep_input_error['JST変換受注時間・JST変換見積回答時間_e']
prep_input_error.loc[prep_input_error['ACE_アンフィット区分'].notnull(),'アンフィット種別'] = prep_input_error['ACE_アンフィット区分']
prep_input_error.loc[prep_input_error['ACE_アンフィット区分'].notnull(),'ACE参照スキーマ'] = prep_input_error['ACE_エラーメッセージコード']
prep_input_error.drop(['JST変換受注日・JST変換見積回答日_e','JST変換受注時間・JST変換見積回答時間_e', 'ACE_アンフィット区分', 'ACE_エラーメッセージコード', '_merge'], axis=1, inplace=True)

#インプットから復活させるRECのインナーコードの先頭2文字をEにする
#納区、UF対象外、エラーコードありは除く
prep_input_error.loc[((prep_input_error['納入区分'] == '00') | (prep_input_error['納入区分'] == '0L')) & (prep_input_error['アンフィット種別'] == '0'),'インナーコード'] = 'EE' + prep_input_error['インナーコード'].str[-9:]
# 見積りUF RECの従来生産拠点フラグを削除
prep_input_error.loc[prep_input_error['見積有効日'].notnull(), '従来生産拠点フラグ'] = ''
#正常処理したRECと復活させるRECの結合
check_input = check_input.append(prep_input_error, sort=False)

#check_inputの件数をカウント
num_check_input=len(check_input)

# FCNT→FCNXへ
check_input.loc[check_input['ACE仕入先コード']=='FCNT', 'ACE仕入先コード'] = 'FCNX'

# 受注日時順に並べ替え
check_input = check_input.sort_values(['JST変換受注日・JST変換見積回答日', 'JST変換受注時間・JST変換見積回答時間', '番号'])

#従来生産拠点のないエラーファイルのみ取り出す
jri_e = pd.merge(error_list, n_jri_e, on='番号', how='inner')

#件数を出力するファイルの件数を取得
num_prep_input = len(prep_input)
num_error=len(prep_input_error[prep_input_error['見積有効日'].isnull()])
num_QT=len(prep_input_error[prep_input_error['見積有効日'].notnull()])
num_sup_ng=len(SUP_NG)

#処理件数を合計
num_total = num_True + num_error + num_QT

#string型にしてから行数格納のリストを作成
num_prep_input = str(num_prep_input)
num_check_input=str(num_check_input)
num_True=str(num_True)
num_error=str(num_error)
num_QT=str(num_QT)
num_jri_e=str(num_jri_e)
num_total = str(num_total)
num_sup_ng = str(num_sup_ng)

num = ['A/準備処理inputREC数：',',',num_prep_input,'\n',
       'B/check_input 行数：',',',num_check_input,'\n',
       'C/RBS対象REC数：',',',num_True,'\n',
       'D/シミュレーション対象REC数：',',',num_error,'\n',
       'E/見積りREC数：',',',num_QT,'\n',
       'C+D+E/処理件数合計：',',',num_total,'\n',
       'F/従来生産拠点フラグなし：',',',num_jri_e,'\n',
       'G/サプライヤコードNG行数：',',',num_sup_ng]

# ファイルアウトプット
check_input.to_csv('check_input.tsv', sep='\t', encoding=font, quotechar='"', line_terminator='\n', index=False)
error_list.to_csv('error_list.tsv', sep='\t', encoding=font, quotechar='"', line_terminator='\n', index=False)
SUP_NG.to_csv('Supplier_CD_NG.tsv', sep='\t', encoding=font, quotechar='"', line_terminator='\n', index=False)
jri_e.to_csv('従来生産拠点なし_error_list.tsv', sep='\t', encoding=font, quotechar='"', line_terminator='\n', index=False)
with open('log.csv', mode='w') as f:
    f.writelines(num)

# tkinter.messagebox.showinfo('UNIONプログラム','Finish！')
print('Finish!')
