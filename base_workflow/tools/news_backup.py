import os
import sys
import json
import akshare as ak
from datetime import datetime
from bs4 import BeautifulSoup
import json
from datetime import datetime

import pandas as pd
def get_crypto_news(symbol: str, max_news: int = 10) -> list:
    """获取并处理加密货币相关新闻

    Args:
        symbol (str): 加密货币符号，如 "BTC"、"ETH"。
        max_news (int, optional): 获取的新闻条数，默认为10条。最大支持100条。

    Returns:
        list: 新闻列表，每条新闻包含标题、内容、发布时间等信息
    """

    # 设置pandas显示选项，确保显示完整内容
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_colwidth', None)
    pd.set_option('display.width', None)

    # 限制最大新闻条数
    max_news = min(max_news, 100)

    # 获取当前日期
    today = datetime.now().strftime("%Y-%m-%d")

    # 构建新闻文件路径
    # project_root = os.path.dirname(os.path.dirname(
    #     os.path.dirname(os.path.abspath(__file__))))
    news_dir = os.path.join("base_workflow", "data", "stock_news")
    print(f"新闻保存目录: {news_dir}")

    # 确保目录存在
    try:
        os.makedirs(news_dir, exist_ok=True)
        print(f"成功创建或确认目录存在: {news_dir}")
    except Exception as e:
        print(f"创建目录失败: {e}")
        return []

    news_file = os.path.join(news_dir, f"{symbol}_news.json")
    print(f"新闻文件路径: {news_file}")

    # 检查是否需要更新新闻
    need_update = True
    if os.path.exists(news_file):
        try:
            with open(news_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if data.get("date") == today:
                    cached_news = data.get("news", [])
                    if len(cached_news) >= max_news:
                        print(f"使用缓存的新闻数据: {news_file}")
                        return cached_news[:max_news]
                    else:
                        print(
                            f"缓存的新闻数量({len(cached_news)})不足，需要获取更多新闻({max_news}条)")
        except Exception as e:
            print(f"读取缓存文件失败: {e}")

    print(f'开始获取{symbol}的新闻数据...')

    try:
        # 获取新闻列表
        news_df = ak.stock_news_em(symbol=symbol)
        if news_df is None or len(news_df) == 0:
            print(f"未获取到{symbol}的新闻数据")
            return []

        print(f"成功获取到{len(news_df)}条新闻")

        # 实际可获取的新闻数量
        available_news_count = len(news_df)
        if available_news_count < max_news:
            print(f"警告：实际可获取的新闻数量({available_news_count})少于请求的数量({max_news})")
            max_news = available_news_count

        # 获取指定条数的新闻（考虑到可能有些新闻内容为空，多获取50%）
        news_list = []
        for _, row in news_df.head(int(max_news * 1.5)).iterrows():
            try:
                # 获取新闻内容
                content = row["新闻内容"] if "新闻内容" in row and not pd.isna(
                    row["新闻内容"]) else ""
                if not content:
                    content = row["新闻标题"]

                # 只去除首尾空白字符
                content = content.strip()
                if len(content) < 10:  # 内容太短的跳过
                    continue

                # 获取关键词
                keyword = row["关键词"] if "关键词" in row and not pd.isna(
                    row["关键词"]) else ""

                # 添加新闻
                news_item = {
                    "title": row["新闻标题"].strip(),
                    "content": content,
                    "publish_time": row["发布时间"],
                    "source": row["文章来源"].strip(),
                    "url": row["新闻链接"].strip(),
                    "keyword": keyword.strip()
                }
                news_list.append(news_item)
                print(f"成功添加新闻: {news_item['title']}")

            except Exception as e:
                print(f"处理单条新闻时出错: {e}")
                continue

        # 按发布时间排序
        news_list.sort(key=lambda x: x["publish_time"], reverse=True)

        # 只保留指定条数的有效新闻
        news_list = news_list[:max_news]

        # 保存到文件
        try:
            save_data = {
                "date": today,
                "news": news_list
            }
            with open(news_file, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            print(f"成功保存{len(news_list)}条新闻到文件: {news_file}")
        except Exception as e:
            print(f"保存新闻数据到文件时出错: {e}")

        return news_list

    except Exception as e:
        print(f"获取新闻数据时出错: {e}")
        return []
    

def run_test(symbol: str, max_news: int = 5):
    print(f"\n开始测试 {symbol} 的新闻获取，最大条数：{max_news}")
    news_list = get_crypto_news(symbol, max_news)

    if not news_list:
        print("未获取到新闻或发生错误。")
        return

    print(f"\n成功获取到 {len(news_list)} 条新闻：")
    for i, news in enumerate(news_list, 1):
        print(f"{i}. {news['publish_time']} | {news['title']} | 来源: {news['source']}")

    # 检查文件保存
    today = datetime.now().strftime("%Y-%m-%d")
    news_file = os.path.join("base_workflow", "data", "stock_news", f"{symbol}_news.json")
    if os.path.exists(news_file):
        print(f"\n新闻文件已保存: {news_file}")
        with open(news_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if data.get("date") == today:
                print("文件中日期正确，文件验证通过。")
            else:
                print("文件中的日期不正确！")
    else:
        print(f"新闻文件未找到: {news_file}")

if __name__ == "__main__":
    # 可以按需测试不同币种和条数
    run_test("BTC", 5)
    run_test("ETH", 3)
