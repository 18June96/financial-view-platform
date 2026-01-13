import pandas as pd
import os
import streamlit as st
import matplotlib.pyplot as plt

#合并不同年份数据到excel表
path = "./" 
data = []
# 遍历文件夹中的所有excel文件
dir = os.listdir(path)  # os.listdir(path)——列出指定路径path下的所有文件/文件夹名称
for file_name in dir:
    #筛选以“Data”开头，“.xlsx”结尾的文件名
    if file_name.startswith("Data") and file_name.endswith(".xlsx"):
        # 构建完整路径
        file_path = os.path.join(path, file_name)
        # 读取Excel文件
        df = pd.read_excel(file_path, usecols=["ts_code", "营业收入", "营业利润"])  # usecols——选择指定列
        # 从文件名提取年份（从"Data2018.xlsx"中提取"2018"）
        year = file_name.replace("Data", "").replace(".xlsx", "")   #去除前缀“.Data”、后缀“.xlsx”
        df["年份"] = year   # 新增“年份”列
        data.append(df)
# 合并所有数据
merged_df = pd.concat(data, ignore_index=True)  # ignore_index=True——重置索引，创建一个从0开始的新索引

# 关联申万行业分类表
info = pd.read_excel('申万行业分类.xlsx', usecols=["股票代码", "新版一级行业", "新版二级行业", "新版三级行业"])
merged_industry = pd.merge(merged_df,info,left_on="ts_code",right_on="股票代码",how="left")
# left_on="ts_code"——左表的关联键 ,right_on="股票代码"——右表的关联键 ，因为两个表的字段名称不同

st.set_page_config(
    page_title="谢卓君_行业应收&利润可视化分析",
    layout='wide',
)

with st.sidebar:
    st.subheader('📚 请选择申万行业级别')
    level = st.selectbox(" ", ['新版一级行业','新版二级行业','新版三级行业'])
    st.subheader('请选择分析类型')
    cla = st.selectbox(" ", ['营业收入','营业利润'])

merged_industry = merged_industry.sort_values(by=[level, "ts_code", "年份"])
# 计算收入增长率,pct_change()——计算每个分组内相邻行（即相邻年份）的百分比变化
merged_industry["营业收入增长率"] = merged_industry.groupby([level, "ts_code"])["营业收入"].pct_change() * 100
# 计算利润增长率
merged_industry["营业利润增长率"] = merged_industry.groupby([level, "ts_code"])["营业利润"].pct_change() * 100
# 填充缺失值,fillna(0)——将NaN值填充为0
merged_industry[["营业收入增长率", "营业利润增长率"]] = merged_industry[["营业收入增长率", "营业利润增长率"]].fillna(0)

st.subheader(f'申万{level}{cla}可视化分析')
st.subheader('行业概况')

if cla == "营业收入":
    df_sum = merged_industry.groupby([level, "年份"]).agg(
        营业收入=("营业收入", lambda x: x.astype(float).sum()),
        上市公司数量=("ts_code", "nunique")
        ).reset_index()
else:
    df_sum = merged_industry.groupby([level, "年份"]).agg(
        营业利润=("营业利润", lambda x: x.astype(float).sum()),
        上市公司数量=("ts_code", "nunique")
        ).reset_index()
#按公式“(当前年份-上一年份)/上一年份”计算增长率
df_sum = df_sum.sort_values([level, "年份"])
growth_col = f"{cla}增长率"

df_sum[growth_col] = (df_sum[cla] - df_sum.groupby(level)[cla].shift(1)) / df_sum.groupby(level)[cla].shift(1) * 100        
#要是上一年没有数据，填充为0
df_sum[growth_col] = df_sum[growth_col].fillna(0)

# 重命名列
df_sum.rename(columns={
    level: "行业名称",
    "年份": "年度"
}, inplace=True)
# 格式化增长率
df_sum[f"{cla}增长率"] = df_sum[f"{cla}增长率"].apply(lambda x: f"{x:.2f}%")

st.dataframe(df_sum, use_container_width=True, hide_index=True)

st.subheader(f'近六年来{cla}增长率最大的八个行业')      

years = sorted(merged_industry["年份"].astype(int).unique())[-6:]
plt.rcParams['font.sans-serif'] = 'Simhei'
fig, axes = plt.subplots(3, 2, figsize=(20, 15))
axes = axes.flatten()
bar_color = "#1f77b4"

for i, year in enumerate(years):
    year_data = merged_industry[merged_industry["年份"].astype(int) == year]
    # 按行业计算增长率均值
    if cla == "营业收入":
        growth_data = year_data.groupby(level)["营业收入增长率"].mean().reset_index()
    else:
        growth_data = year_data.groupby(level)["营业利润增长率"].mean().reset_index()
    
    top8 = growth_data.nlargest(8, f"{cla}增长率").sort_values(by=f"{cla}增长率")
    axes[i].bar(top8[level], top8[f"{cla}增长率"], color=bar_color)
    axes[i].set_title(f"{year}年{cla}增长率Top8行业", fontsize=14)
    axes[i].set_xlabel("行业", fontsize=12)
    axes[i].set_ylabel(f"{cla}增长率（%）", fontsize=12)
    axes[i].grid(axis='x', linestyle='--', alpha=0.6)
    
plt.tight_layout()
st.pyplot(fig)
