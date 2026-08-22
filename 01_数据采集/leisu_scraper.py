#!/usr/bin/env python3
"""
雷速体育(leisu.com)数据抓取器
使用Playwright绕过阿里云WAF防护
"""

import asyncio
import json
import sys

async def scrape_leisu_team(team_id):
    """
    抓取雷速体育球队数据
    
    Args:
        team_id: 球队ID，如 11746
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("❌ 需要安装playwright:")
        print("   pip install playwright")
        print("   playwright install chromium")
        return None
    
    url = f"https://www.leisu.com/data/zuqiu/team-{team_id}/lineup"
    print(f"📡 正在抓取: {url}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()
        
        try:
            # 访问页面
            await page.goto(url, wait_until='networkidle', timeout=30000)
            
            # 等待WAF挑战完成
            await page.wait_for_timeout(5000)
            
            # 检查是否还在WAF页面
            content = await page.content()
            if 'aliyun_waf' in content:
                print("⚠️ WAF挑战未完成，等待更长时间...")
                await page.wait_for_timeout(10000)
                content = await page.content()
            
            # 提取数据
            data = await extract_team_data(page)
            
            print("✅ 数据抓取成功!")
            return data
            
        except Exception as e:
            print(f"❌ 抓取失败: {e}")
            return None
        
        finally:
            await browser.close()


async def extract_team_data(page):
    """从页面提取球队数据"""
    data = {
        'team_name': '',
        'players': {
            'forwards': [],
            'midfielders': [],
            'defenders': [],
            'goalkeepers': []
        },
        'coaches': []
    }
    
    try:
        # 获取球队名称
        team_name = await page.query_selector('h1, .team-name, [class*="team"]')
        if team_name:
            data['team_name'] = await team_name.text_content()
        
        # 获取球员数据
        player_rows = await page.query_selector_all('tr, .player-row, [class*="player"]')
        for row in player_rows:
            text = await row.text_content()
            if text and len(text.strip()) > 5:
                # 解析球员信息
                parts = text.strip().split()
                if len(parts) >= 3:
                    player_info = {
                        'raw_text': text.strip()
                    }
                    data['players']['forwards'].append(player_info)
        
        # 获取教练信息
        coach_section = await page.query_selector('[class*="coach"], .staff')
        if coach_section:
            coach_text = await coach_section.text_content()
            data['coaches'].append({'raw_text': coach_text})
        
    except Exception as e:
        print(f"数据提取警告: {e}")
    
    return data


async def scrape_leisu_match(match_id):
    """
    抓取雷速体育比赛数据
    
    Args:
        match_id: 比赛ID
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("❌ 需要安装playwright")
        return None
    
    url = f"https://www.leisu.com/data/zuqiu/match-{match_id}"
    print(f"📡 正在抓取: {url}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            await page.goto(url, wait_until='networkidle', timeout=30000)
            await page.wait_for_timeout(5000)
            
            content = await page.content()
            return content
            
        except Exception as e:
            print(f"❌ 抓取失败: {e}")
            return None
        
        finally:
            await browser.close()


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法:")
        print("  python leisu_scraper.py team <team_id>")
        print("  python leisu_scraper.py match <match_id>")
        print("")
        print("示例:")
        print("  python leisu_scraper.py team 11746  # 抓取球队数据")
        print("  python leisu_scraper.py match 12345  # 抓取比赛数据")
        return
    
    action = sys.argv[1]
    
    if action == 'team' and len(sys.argv) >= 3:
        team_id = sys.argv[2]
        result = asyncio.run(scrape_leisu_team(team_id))
        if result:
            print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif action == 'match' and len(sys.argv) >= 3:
        match_id = sys.argv[2]
        result = asyncio.run(scrape_leisu_match(match_id))
        if result:
            print(result[:1000])  # 只打印前1000字符
    
    else:
        print("❌ 无效参数")


if __name__ == '__main__':
    main()
