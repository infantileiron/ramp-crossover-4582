export const roles = { reviewer: '业务复核员', analyst: '数据分析员', viewer: '观察员' };
export const sequences = { AB: ['A', 'B'], BA: ['B', 'A'] };
export const states = { queued: '等待计算', ready: '待复核', failed: '运行失败', published: '已发布' };
export const decisions = { retest: '补测后复核', retain: '保留现牌', pilot: '安排局部试挂' };
