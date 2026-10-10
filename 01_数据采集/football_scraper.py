#!/usr/bin/env python3
"""
足球数据自动抓取器
支持：懂球帝API、咪咕视频API、雷速体育(浏览器自动化)
"""

import json
import subprocess
import sys

class FootballDataScraper:
    """足球数据抓取器"""
    
    def __init__(self):
        self.dongqiudi_api = "https://api.dongqiudi.com/data/tab/league/new/61"
        self.migu_api = "https://webapi.miguvideo.com/gateway/vms-livedata/competition-score/v2/batch-live-score"
    
    def fetch_dongqiudi(self):
        """抓取懂球帝世界杯数据"""
        try:
            result = subprocess.run(
                ['curl', '-s', '-L', '--max-time', '30', self.dongqiudi_api, 
                 '-H', 'User-Agent: Mozilla/5.0'],
                capture_output=True, text=True
            )
            data = json.loads(result.stdout)
            return data.get('list', [])
        except Exception as e:
            print(f"懂球帝API错误: {e}")
            return []
    
    def find_match(self, home_team, away_team):
        """搜索特定比赛"""
        matches = self.fetch_dongqiudi()
        results = []
        
        for match in matches:
            home = match.get('team_A_name', '')
            away = match.get('team_B_name', '')
            
            if home_team in home or away_team in away:
                results.append({
                    'match_id': match.get('match_id'),
                    'home': home,
                    'away': away,
                    'date': match.get('date_utc'),
                    'time': match.get('time_utc'),
                    'status': match.get('status'),
                    'score': f"{match.get('fs_A', '?')}-{match.get('fs_B', '?')}",
                    'gameweek': match.get('gameweek'),
                    'competition': match.get('competition_name')
                })
        
        return results
    
    def get_team_matches(self, team_name):
        """获取某队所有比赛"""
        matches = self.fetch_dongqiudi()
        results = []
        
        for match in matches:
            home = match.get('team_A_name', '')
            away = match.get('team_B_name', '')
            
            if team_name in home or team_name in away:
                results.append({
                    'match_id': match.get('match_id'),
                    'home': home,
                    'away': away,
                    'date': match.get('date_utc'),
                    'score': f"{match.get('fs_A', '?')}-{match.get('fs_B', '?')}",
                    'status': match.get('status'),
                    'gameweek': match.get('gameweek')
                })
        
        return results
    
    def scrape_leisu_with_playwright(self, url):
        """使用Playwright抓取雷速体育数据"""
        try:
            import asyncio
            from playwright.async_api import async_playwright
            
            async def _scrape():
                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=True)
                    page = await browser.new_page()
                    await page.goto(url, wait_until='networkidle')
                    await page.wait_for_timeout(3000)
                    content = await page.content()
                    await browser.close()
                    return content
            
            return asyncio.run(_scrape())
        except ImportError:
            print("需要安装playwright: pip install playwright && playwright install chromium")
            return None
        except Exception as e:
            print(f"Playwright错误: {e}")
            return None


def main():
    """主函数"""
    scraper = FootballDataScraper()
    
    # 示例：搜索巴西vs日本
    print("=== 搜索巴西 vs 日本 ===")
    matches = scraper.find_match('巴西', '日本')
    for m in matches:
        print(f"{m['date']} | {m['home']} vs {m['away']} | {m['score']} | {m['status']}")
    
    print("\n=== 搜索德国所有比赛 ===")
    matches = scraper.get_team_matches('德国')
    for m in matches:
        print(f"GW{m['gameweek']} | {m['date']} | {m['home']} vs {m['away']} | {m['score']}")


if __name__ == '__main__':
    main()
