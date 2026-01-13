# 上市公司行业营收与利润分析系统技术文档
## 一、项目概述  
　　本系统是一个基于 Streamlit 的交互式财务数据分析工具,通过合并多年度的财务数据，结合申万行业分类标准，实现对各行业“营业收入”和“营业利润”的统计分析、增长率计算及可视化展示。
## 二、技术架构  
　　核心框架: Streamlit (Web 界面构建)  
　　数据处理: Pandas (数据清洗、合并、分组计算)  
　　可视化: Matplotlib (柱状图)  
　　文件操作: Python 内置 os 模块  
## 三、数据源与文件结构  
系统运行依赖于当前目录下的特定文件结构：  
**1.财务数据文件:**  
　　命名规则: 以 Data 开头，以 .xlsx 结尾（例如：Data2020.xlsx, Data2021.xlsx）。  
　　关键字段: ts_code (股票代码), 营业收入, 营业利润。  
**2.行业分类文件:**  
　　文件名: 申万行业分类.xlsx  
　　关键字段: 股票代码, 新版一级行业, 新版二级行业, 新版三级行业。  
## 四、核心功能模块  
该程序的执行流程主要分为四个阶段：数据合并、数据关联、交互式分析和可视化展示。  
### 4.1 数据合并模块  
**功能：** 自动发现并合并指定目录下的多份年度财务报表。  
实现逻辑:  
　　1.目录遍历: 使用 os.listdir() 扫描当前路径;  
　　2.文件筛选: 通过 startswith("Data") 和 endswith(".xlsx") 过滤出财务数据文件;  
　　3.年份提取: 利用字符串的 replace() 方法，从文件名（如 Data2023.xlsx）中剥离出年份;  
　　4.数据整合: 读取每个文件的指定列，并新增一个 年份 列用于标识数据来源，最后使用 pd.concat() 将所有数据纵向合并为一个大的数据框。   
```python
import pandas as pd
import os
 
# 合并不同年份数据到excel表
path = "./" 
data = []
# 遍历文件夹中的所有excel文件
dir = os.listdir(path)    # os.listdir(path)——列出指定路径path下的所有文件/文件夹名称
for file_name in dir:
    # 筛选以“Data”开头，“.xlsx”结尾的文件名
    if file_name.startswith("Data") and file_name.endswith(".xlsx"):
        # 构建完整路径
        file_path = os.path.join(path, file_name)
        # 读取Excel文件
        df = pd.read_excel(file_path, usecols=["ts_code", "营业收入", "营业利润"])  # usecols——选择指定列
        # 从文件名提取年份（从"Data2018.xlsx"中提取"2018"）
        year = file_name.replace("Data", "").replace(".xlsx", "")   #去除前缀“.Data”、后缀“.xlsx”，只留下“2018”
        df["年份"] = year   # 新增“年份”列
        data.append(df)
# 合并所有数据
merged_df = pd.concat(data, ignore_index=True)  # ignore_index=True——重置索引，创建一个从0开始的新索引
```
### 4.2 数据关联模块  
**功能：** 将合并后的财务数据与行业分类信息进行关联，以便按行业维度进行统计。  
实现逻辑:  
　　1.读取 申万行业分类.xlsx；  
　　2.使用 pd.merge() 将合并后的财务数据（左表）与行业表（右表）进行左连接；  
　　3.关联键: 左表的 ts_code 与右表的 股票代码；    
　　4.结果: 得到了包含股票代码、财务指标、所属行业级别及年份的宽表。    
```python
# 加载申万行业分类标准
info = pd.read_excel('申万行业分类.xlsx', 
                     usecols=["股票代码", "新版一级行业", "新版二级行业", "新版三级行业"])
 
# 双表关联：将财务数据映射到行业分类
merged_with_industry = pd.merge(
    merged_df,           # 财务数据表
    info,                # 行业分类表
    left_on="ts_code",   # 财务数据中的股票代码
    right_on="股票代码",  # 行业表中的股票代码
    how="left"           # 左连接，保留所有财务数据
)
```
### 4.3 增长率计算模块  
**功能：** 计算个股及行业的增长率指标。  
算法逻辑:  
　　1.数据排序: 按照选定的行业级别、股票代码和年份进行排序，确保时间序列的连续性；  
　　2.个股增长率: 使用 groupby().pct_change() 计算每只股票相邻年份的增长率；  
　　3.行业增长率: 在分组汇总后，使用 shift(1) 计算行业总值的同比增长率；  
　　4.缺失值处理: 使用 fillna(0) 处理因无法计算增长率（如第一年数据）产生的空值。  
**营业收入增长率 = (本年营业收入 - 上年营业收入) / 上年营业收入 × 100%**  
**营业利润增长率 = (本年营业利润 - 上年营业利润) / 上年营业利润 × 100%**  
```python
# 按行业和公司排序，为分组计算做准备
merged_with_industry = merged_with_industry.sort_values(
    by=[level, "ts_code", "年份"]
)
 
# 计算营业收入同比增长率
merged_with_industry["营业收入增长率"] = (
    merged_with_industry.groupby([level, "ts_code"])["营业收入"]
    .pct_change() * 100
)
 
# 计算营业利润同比增长率
merged_with_industry["营业利润增长率"] = (
    merged_with_industry.groupby([level, "ts_code"])["营业利润"]
    .pct_change() * 100
)
 
# 处理缺失值（首年数据无增长率）
merged_with_industry[["营业收入增长率", "营业利润增长率"]] = (
    merged_with_industry[["营业收入增长率", "营业利润增长率"]].fillna(0)
)
```
### 4.4 Streamlit 交互界面模块  
**功能：** 构建用户友好的 Web 交互界面。  
布局结构:  
　　**侧边栏:**  
　　　　行业级别选择: 下拉框选择 新版一级行业、新版二级行业 或 新版三级行业。  
　　　　分析指标选择: 下拉框选择 营业收入 或 营业利润。   
　　**主区域:**  
　　　　行业概况表格: 展示所选指标下，各行业每年的总和、公司数量及增长率。  
　　　　Top 8 柱状图: 展示最近 6 年中，每年增长率最高的 8 个行业的对比图。  
<img width="1860" height="885" alt="image" src="https://github.com/user-attachments/assets/cb427325-5e42-4a67-a769-08620be9309a" />

## 五、关键代码逻辑解析
### 5.1 动态文件读取与合并
   **作用**：自动适配新增的年度数据文件，无需修改代码即可处理新一年的数据。  
```python
for file_name in dir:
    if file_name.startswith("Data") and file_name.endswith(".xlsx"):
        file_path = os.path.join(path, file_name)
        df = pd.read_excel(file_path, usecols=["ts_code", "营业收入", "营业利润"])
        year = file_name.replace("Data", "").replace(".xlsx", "")
        df["年份"] = year
        data.append(df)
merged_df = pd.concat(data, ignore_index=True)
```
### 5.2 分组聚合  
根据用户选择的指标（营业收入/营业利润）动态执行不同的聚合计算。  
```python
if cla == "营业收入":
    df_sum = merged_industry.groupby([level, "年份"]).agg(
        营业收入=("营业收入", lambda x: x.astype(float).sum()),
        上市公司数量=("ts_code", "nunique")
    ).reset_index()
```
## 六、可视化图表说明
**图表类型:** 堆叠柱状图 (Matplotlib)。  
**布局:** 3行2列的子图网格，展示最近6年的数据。  
**数据处理:**    
　　1.每年的数据按所选指标的平均增长率进行分组计算。  
　　2.使用 nlargest(8) 筛选出增长率最高的前8个行业。  
　　3.使用 sort_values() 对柱状图进行排序，便于阅读。  
**样式设置:**   
　　中文支持：plt.rcParams['font.sans-serif'] = 'Simhei'。  
　　网格线：添加垂直网格线辅助读数。  
## 七、注意事项
　　文件格式: 财务数据文件必须是 .xlsx 格式，且文件名必须严格遵循 Data{年份}.xlsx 的命名规范。  
　　数据类型: 代码中对财务数据进行了 astype(float) 转换，确保数据中不含无法转换的非数值字符。  
　　性能: 如果数据量非常大，groupby().pct_change() 和图表渲染可能会有轻微延迟。  
　　空值: 代码简单地将增长率空值填充为 0，在实际业务分析中，可能需要根据具体情况（如新上市、扭亏为盈）进行更细致的处理。  
## 八、总结
　　该项目展示了如何利用 Python 自动化处理散落在多个文件中的财务数据，并通过简单的 Web 界面让用户能够灵活地从不同维度（行业级别、指标类型）进行数据探索和可视化，具有很强的实用性和扩展性。
