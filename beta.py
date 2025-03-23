import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import statsmodels.api as sm


def calculate_beta_and_stats(market_excess_returns, fund_excess_returns):
    X = market_excess_returns.values.reshape(-1, 1)
    y = fund_excess_returns.values
    model = LinearRegression()
    model.fit(X, y)
    beta = model.coef_[0]
    r_squared = model.score(X, y)

    # 使用 statsmodels 计算显著性
    X_sm = sm.add_constant(X)
    model_sm = sm.OLS(y, X_sm).fit()
    p_value = model_sm.pvalues[1]

    return beta, r_squared, p_value


# 读取 Excel 文件
excel_file = pd.ExcelFile('data1.xlsx')

# 获取市场指数与期货数据
market_data = excel_file.parse('市场指数与期货数据')
market_data['日期'] = pd.to_datetime(market_data['日期'])
market_data.set_index('日期', inplace=True)

# 获取基金数据
fund_data = excel_file.parse('基金数据')
fund_data['日期'] = pd.to_datetime(fund_data['日期'])
fund_data.set_index('日期', inplace=True)

# 筛选指定基金代码
fund_data = fund_data[fund_data['基金代码'] == 5827]
# 合并数据
merged_data = pd.merge(market_data[['hs300收益率', '无风险收益率', 'hs300期货收盘价']],
                       fund_data[['累计净值']],
                       left_index=True, right_index=True, how='inner')

# 计算每日无风险日收益率
risk_free_daily_returns = (1 + merged_data['无风险收益率']) ** (1 / 252) - 1

# 计算每日市场收益率并减去当日无风险利率
market_daily_returns = merged_data['hs300收益率']
market_excess_returns = market_daily_returns - risk_free_daily_returns
# 删除第一个数据
market_excess_returns = market_excess_returns[1:]

# 计算每日基金收益率并减去当日无风险利率
fund_daily_returns = merged_data['累计净值'].pct_change().dropna()
fund_excess_returns = fund_daily_returns - risk_free_daily_returns.loc[fund_daily_returns.index]

hs300_futures = merged_data['hs300期货收盘价']

# 按每三个月分组计算 beta
quarters = pd.date_range(start='2023-12-31', end='2024-12-31', freq='Q')
num = [41144000000,39036000000,43835000000,37498000000]
for i in range(len(quarters) - 1):
    start_date = quarters[i]
    end_date = quarters[i + 1]
    quarterly_market = market_excess_returns[(market_excess_returns.index >= start_date) & (
            market_excess_returns.index < end_date)]
    quarterly_fund = fund_excess_returns[(fund_excess_returns.index >= start_date) & (
            fund_excess_returns.index < end_date)]
    quarterly_hs300_futures = hs300_futures[(hs300_futures.index >= start_date) & (
            hs300_futures.index < end_date)].mean()
    if len(quarterly_market) > 0 and len(quarterly_fund) > 0:
        beta, r_squared, p_value = calculate_beta_and_stats(quarterly_market, quarterly_fund)
        print(
            f"从 {start_date.strftime('%Y-%m-%d')} 到 {end_date.strftime('%Y-%m-%d')} 的 beta 值: {beta:.4f}, R^2 值: {r_squared:.4f}, p 值: {p_value:.20f}")
    else:
        print(
            f"从 {start_date.strftime('%Y-%m-%d')} 到 {end_date.strftime('%Y-%m-%d')} 数据不足，无法计算 beta 值。")
    N = int(beta * num[i] / (quarterly_hs300_futures * 300))
    print(f"期货合约数量{N}")
    new_Beta = beta - ((float(N)) * 300 * quarterly_hs300_futures / num[i])
    print(f"新的beta值{new_Beta}")