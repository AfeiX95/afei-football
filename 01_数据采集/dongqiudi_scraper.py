#!/usr/bin/env python3
"""
懂球帝数据自动抓取器 v2.0
支持：比赛数据、新闻资讯、球队信息、赔率指数
"""

import json
import subprocess
import sys
from datetime import datetime

class DongqiudiScraper:
    """懂球帝数据抓取器"""
    
    def __init__(self):
        self.match_api = "https://api.dongqiudi.com/data/tab/league/new/61"
        self.news_api = "https://api.dongqiudi.com/app/tabs/iphone/1.json"
        self.headers = "-H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)'"
    
    def _fetch(self, url):
        """通用请求方法"""
        try:
            result = subprocess.run(
                ['curl', '-s', '-L', '--max-time', '30', url, 
                 '-H', 'User-Agent: Mozilla/5.0'],
                capture_output=True, text=True
            )
            return json.loads(result.stdout)
        except Exception as e:
            print(f"请求失败: {e}")
            return None
    
    # ==================== 比赛数据 ====================
    
    def get_all_matches(self):
        """获取世界杯所有比赛"""
        data = self._fetch(self.match_api)
        if not data:
            return []
        return data.get('list', [])
    
    def find_match(self, home_team, away_team):
        """搜索特定比赛"""
        matches = self.get_all_matches()
        results = []
        
        for match in matches:
            home = match.get('team_A_name', '')
            away = match.get('team_B_name', '')
            
            if home_team in home and away_team in away:
                results.append(self._parse_match(match))
        
        return results
    
    def get_team_matches(self, team_name):
        """获取某队所有比赛"""
        matches = self.get_all_matches()
        results = []
        
        for match in matches:
            home = match.get('team_A_name', '')
            away = match.get('team_B_name', '')
            
            if team_name in home or team_name in away:
                results.append(self._parse_match(match))
        
        return results
    
    def _parse_match(self, match):
        """解析比赛数据"""
        return {
            'match_id': match.get('match_id'),
            'home': match.get('team_A_name', ''),
            'away': match.get('team_B_name', ''),
            'date': match.get('date_utc', ''),
            'time': match.get('time_utc', ''),
            'status': match.get('status', ''),
            'score': f"{match.get('fs_A', '?')}-{match.get('fs_B', '?')}",
            'half_score': f"{match.get('hts_A', '?')}-{match.get('hts_B', '?')}",
            'gameweek': match.get('gameweek', ''),
            'competition': match.get('competition_name', ''),
            'rank_home': match.get('rank_A', ''),
            'rank_away': match.get('rank_B', ''),
            'odds_home': match.get('home', ''),
            'odds_draw': match.get('draw', ''),
            'odds_away': match.get('away', ''),
            'handicap': match.get('hdp', ''),
            'over': match.get('over', ''),
            'under': match.get('under', ''),
            'corner_home': match.get('corner_A', ''),
            'corner_away': match.get('corner_B', ''),
            'red_home': match.get('rc_A', ''),
            'red_away': match.get('rc_B', ''),
            'yellow_home': match.get('yc_A', ''),
            'yellow_away': match.get('yc_B', ''),
            'shots_home': match.get('as_A', ''),
            'shots_away': match.get('as_B', ''),
            'events_home': match.get('team_A_events', []),
            'events_away': match.get('team_B_events', []),
        }
    
    # ==================== 新闻资讯 ====================
    
    def get_news(self, limit=20):
        """获取最新新闻"""
        data = self._fetch(self.news_api)
        if not data:
            return []
        
        articles = data.get('articles', [])
        results = []
        
        for article in articles[:limit]:
            results.append({
                'id': article.get('id'),
                'title': article.get('title', ''),
                'description': article.get('description', ''),
                'published_at': article.get('published_at', ''),
                'category': article.get('category', ''),
                'tags': article.get('secondary_category', []),
                'comments': article.get('comments_total', 0),
                'url': article.get('share', ''),
                'thumb': article.get('thumb', ''),
                'author': article.get('author_name', ''),
            })
        
        return results
    
    def search_news(self, keyword, limit=10):
        """搜索相关新闻"""
        news = self.get_news(limit=50)
        results = []
        
        for article in news:
            title = article.get('title', '')
            desc = article.get('description', '')
            tags = ' '.join(article.get('tags', []))
            
            if keyword in title or keyword in desc or keyword in tags:
                results.append(article)
        
        return results[:limit]
    
    # ==================== 球队数据 ====================
    
    def get_team_stats(self, team_name):
        """获取球队统计数据"""
        matches = self.get_team_matches(team_name)
        
        if not matches:
            return None
        
        stats = {
            'team': team_name,
            'total_matches': len(matches),
            'wins': 0,
            'draws': 0,
            'losses': 0,
            'goals_for': 0,
            'goals_against': 0,
            'home_matches': 0,
            'away_matches': 0,
            'home_wins': 0,
            'away_wins': 0,
            'recent_form': [],
            'matches': []
        }
        
        for match in matches:
            is_home = team_name in match['home']
            score_parts = match['score'].split('-')
            
            if len(score_parts) == 2:
                try:
                    gf = int(score_parts[0]) if is_home else int(score_parts[1])
                    ga = int(score_parts[1]) if is_home else int(score_parts[0])
                    
                    stats['goals_for'] += gf
                    stats['goals_against'] += ga
                    
                    if gf > ga:
                        stats['wins'] += 1
                        stats['recent_form'].append('W')
                        if is_home:
                            stats['home_wins'] += 1
                    elif gf == ga:
                        stats['draws'] += 1
                        stats['recent_form'].append('D')
                    else:
                        stats['losses'] += 1
                        stats['recent_form'].append('L')
                    
                    if is_home:
                        stats['home_matches'] += 1
                    else:
                        stats['away_matches'] += 1
                    
                    stats['matches'].append(match)
                except ValueError:
                    pass
        
        # 计算统计
        total = stats['total_matches']
        if total > 0:
            stats['win_rate'] = round(stats['wins'] / total * 100, 1)
            stats['avg_goals_for'] = round(stats['goals_for'] / total, 2)
            stats['avg_goals_against'] = round(stats['goals_against'] / total, 2)
            stats['goal_diff'] = stats['goals_for'] - stats['goals_against']
        
        return stats
    
    # ==================== 对阵分析 ====================
    
    def get_match_analysis(self, home_team, away_team):
        """获取完整对阵分析数据"""
        print(f"📊 正在分析: {home_team} vs {away_team}")
        
        # 1. 搜索比赛
        matches = self.find_match(home_team, away_team)
        
        # 2. 获取两队数据
        home_stats = self.get_team_stats(home_team)
        away_stats = self.get_team_stats(away_team)
        
        # 3. 搜索相关新闻
        home_news = self.search_news(home_team, limit=5)
        away_news = self.search_news(away_team, limit=5)
        match_news = self.search_news(f"{home_team}vs{away_team}", limit=5)
        
        # 4. 汇总
        analysis = {
            'match': matches[0] if matches else None,
            'home_stats': home_stats,
            'away_stats': away_stats,
            'news': {
                'home': home_news,
                'away': away_news,
                'match': match_news,
            }
        }
        
        return analysis
    
    # ==================== 输出 ====================
    
    def print_match_info(self, match):
        """打印比赛信息"""
        if not match:
            print("未找到比赛数据")
            return
        
        print(f"═══════════════════════════════════════")
        print(f"比赛ID: {match['match_id']}")
        print(f"对阵: {match['home']} vs {match['away']}")
        print(f"日期: {match['date']} {match['time']}")
        print(f"状态: {match['status']}")
        print(f"比分: {match['score']} (半场: {match['half_score']})")
        print(f"轮次: 第{match['gameweek']}轮")
        print(f"排名: {match['rank_home']} vs {match['rank_away']}")
        print(f"赔率: 主{match['odds_home']} / 平{match['odds_draw']} / 客{match['odds_away']}")
        print(f"角球: {match['corner_home']} vs {match['corner_away']}")
        print(f"红牌: {match['red_home']} vs {match['red_away']}")
        print(f"黄牌: {match['yellow_home']} vs {match['yellow_away']}")
        print(f"射门: {match['shots_home']} vs {match['shots_away']}")
        print(f"═══════════════════════════════════════")
    
    def print_team_stats(self, stats):
        """打印球队统计"""
        if not stats:
            print("未找到球队数据")
            return
        
        print(f"┌─────────────────────────────────────┐")
        print(f"│ {stats['team']} 球队数据")
        print(f"├─────────────────────────────────────┤")
        print(f"│ 总场次: {stats['total_matches']}")
        print(f"│ 战绩: {stats['wins']}W {stats['draws']}D {stats['losses']}L ({stats.get('win_rate', 0)}%)")
        print(f"│ 进球/失球: {stats['goals_for']}/{stats['goals_against']} (净胜{stats.get('goal_diff', 0)})")
        print(f"│ 场均进球: {stats.get('avg_goals_for', 0)} | 场均失球: {stats.get('avg_goals_against', 0)}")
        print(f"│ 主场: {stats['home_matches']}场 {stats['home_wins']}胜")
        print(f"│ 客场: {stats['away_matches']}场 {stats['away_wins']}胜")
        print(f"│ 近况: {''.join(stats['recent_form'][-10:])}")
        print(f"└─────────────────────────────────────┘")
    
    def print_full_analysis(self, home_team, away_team):
        """打印完整分析"""
        analysis = self.get_match_analysis(home_team, away_team)
        
        print(f"\n{'='*60}")
        print(f"  {home_team} vs {away_team} - 全维度数据分析")
        print(f"{'='*60}\n")
        
        # 比赛信息
        if analysis['match']:
            print("【比赛信息】")
            self.print_match_info(analysis['match'])
        
        # 主队数据
        print(f"\n【{home_team} 球队数据】")
        self.print_team_stats(analysis['home_stats'])
        
        # 客队数据
        print(f"\n【{away_team} 球队数据】")
        self.print_team_stats(analysis['away_stats'])
        
        # 新闻
        print(f"\n【相关资讯】")
        for news in analysis['news'].get('match', []):
            print(f"  📰 {news['title']}")
            print(f"     {news['published_at']} | {news['comments']}评论")
        
        for news in analysis['news'].get('home', [])[:3]:
            print(f"  📰 [{home_team}] {news['title']}")
        
        for news in analysis['news'].get('away', [])[:3]:
            print(f"  📰 [{away_team}] {news['title']}")
        
        return analysis


def main():
    """主函数"""
    scraper = DongqiudiScraper()
    
    if len(sys.argv) < 2:
        print("用法:")
        print("  python dongqiudi_scraper.py match <主队> <客队>  # 搜索比赛")
        print("  python dongqiudi_scraper.py team <队名>          # 球队数据")
        print("  python dongqiudi_scraper.py news [关键词]        # 新闻资讯")
        print("  python dongqiudi_scraper.py analyze <主队> <客队> # 完整分析")
        print("")
        print("示例:")
        print("  python dongqiudi_scraper.py analyze 巴西 日本")
        print("  python dongqiudi_scraper.py analyze 德国 巴拉圭")
        print("  python dongqiudi_scraper.py team 德国")
        print("  python dongqiudi_scraper.py news 世界杯")
        return
    
    action = sys.argv[1]
    
    if action == 'match' and len(sys.argv) >= 4:
        home, away = sys.argv[2], sys.argv[3]
        matches = scraper.find_match(home, away)
        for m in matches:
            scraper.print_match_info(m)
    
    elif action == 'team' and len(sys.argv) >= 3:
        team = sys.argv[2]
        stats = scraper.get_team_stats(team)
        scraper.print_team_stats(stats)
    
    elif action == 'news':
        keyword = sys.argv[2] if len(sys.argv) >= 3 else ''
        if keyword:
            news = scraper.search_news(keyword)
        else:
            news = scraper.get_news()
        for n in news:
            print(f"📰 {n['title']}")
            print(f"   {n['published_at']} | {n['comments']}评论 | {n['url']}")
    
    elif action == 'analyze' and len(sys.argv) >= 4:
        home, away = sys.argv[2], sys.argv[3]
        scraper.print_full_analysis(home, away)
    
    else:
        print("❌ 无效参数")


if __name__ == '__main__':
    main()
