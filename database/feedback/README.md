# 赛后验证数据存储
# 每场比赛一条记录
database/feedback/matches/
  2026-07-16_哥德堡vs索尔纳.json   # 预测+赛后记录
  2026-07-16_奥勒松vs莫尔德.json
  ...

# 短周期滑动窗口
database/feedback/short_term/
  2026-07-16_window.json            # 最近20场的汇总

# 长周期校准
database/feedback/long_term/
  2026-10-01_calibration.json       # 满100场触发

# 权重调整历史
database/weights/
  2026-07-16_weights_v1.0.json     # 初始权重
  2026-10-01_weights_v1.1.json     # 第一次校准后
