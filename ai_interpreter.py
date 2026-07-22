# -*- coding: utf-8 -*-
"""AI 解释引擎 — DeepSeek API 驱动，本地 JSON 缓存，静态兜底

可插拔设计：
  - 有 API Key → AI 生成"凤年真人详解"段落
  - 无 API Key / 调用失败 → 返回 None，上游使用静态模板

缓存策略：
  - MD5(module + sorted_json(data)) → cache/ 目录
  - 90 天 TTL，过期自动刷新
  - 缓存命中直接返回，不调用 API
"""

import os
import json
import hashlib
import time
from datetime import datetime, timezone
from pathlib import Path

# ============================================================
# 常量
# ============================================================
BASE_DIR = Path(__file__).parent
CACHE_DIR = Path(os.environ.get("CACHE_DIR", str(BASE_DIR / "cache")))
CACHE_TTL_DAYS = 90  # 缓存有效期（天）

# DeepSeek API 配置（OpenAI 兼容）
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

# 凤年真人 System Prompt
SYSTEM_PROMPT = """你是一位精通玄学的道长，道号「凤年真人」，幼入玄门，师承龙虎山正一脉，遍览群经三十载，通晓六爻八卦、四柱八字、大六壬、奇门遁甲诸术。

你的语言风格：
- 自称"贫道"，称用户为"道友"或"善信"
- 半文半白，兼具古风与通俗
- 在专业分析中融入道家哲学智慧
- 语气平和、慈悲、不妄断，留有余地
- 分析深入但有温度，不堆砌术语

核心原则：
- 天机不可尽泄，仅供善信参考斟酌
- 知命而不认命，顺应时势者昌
- 每一段分析末尾可加一句道家哲理或祝福

输出要求：
- 纯文本输出，严禁使用任何 markdown 格式
- 不要使用 # * - ` ``` 等符号
- 不要使用数字序号如 1. 2. 3.
- 用中文逗号句号分段，用空行分隔不同主题
- 300-500 字为佳
- 条理清晰，分段自然"""

# ============================================================
# 缓存工具
# ============================================================
def _make_cache_key(module, data_dict):
    """生成缓存键：MD5(module + 排序后的 JSON)"""
    raw = module + json.dumps(data_dict, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.md5(raw.encode('utf-8')).hexdigest()


def _cache_get(module, data_dict):
    """读取缓存，返回文本或 None（未命中/过期）"""
    key = _make_cache_key(module, data_dict)
    cache_file = CACHE_DIR / f"{module}_{key}.json"

    if not cache_file.exists():
        return None

    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            cached = json.load(f)
    except (json.JSONDecodeError, OSError):
        return None

    # 检查 TTL
    created_str = cached.get("created", "")
    if created_str:
        try:
            created = datetime.fromisoformat(created_str)
            age_days = (datetime.now(timezone.utc).replace(tzinfo=None) - created.replace(tzinfo=None)).days
            if age_days > CACHE_TTL_DAYS:
                cache_file.unlink(missing_ok=True)
                return None
        except (ValueError, OSError):
            pass

    return cached.get("text")


def _cache_set(module, data_dict, text):
    """写入缓存"""
    key = _make_cache_key(module, data_dict)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"{module}_{key}.json"

    cached = {
        "text": text,
        "created": datetime.now(timezone.utc).isoformat(),
        "module": module,
    }
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(cached, f, ensure_ascii=False)


# ============================================================
# AI 解释器
# ============================================================
class AIInterpreter:
    """AI 解释器单例"""

    def __init__(self):
        self._client = None
        self._enabled = None
        self._model = None
        self._api_key = None

    # ---- 初始化 ----
    def _init_client(self):
        """延迟初始化 OpenAI 客户端"""
        if self._enabled is not None:
            return

        # 读取环境变量（优先 .env，其次系统环境变量）
        api_key = os.environ.get("DEEPSEEK_API_KEY", "")
        enabled = os.environ.get("AI_API_ENABLED", "").lower()
        model = os.environ.get("AI_API_MODEL", "deepseek-chat")

        self._api_key = api_key
        self._model = model

        if not api_key or enabled == "false":
            self._enabled = False
            return

        try:
            from openai import OpenAI
            self._client = OpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL)
            self._enabled = True
        except ImportError:
            print("[AI] openai 库未安装，AI 功能不可用。pip install openai")
            self._enabled = False
        except Exception as e:
            print(f"[AI] 初始化失败: {e}")
            self._enabled = False

    @property
    def enabled(self):
        """AI 功能是否可用"""
        self._init_client()
        return self._enabled

    # ---- 核心方法 ----
    def interpret(self, module, data_dict, use_cache=True):
        """主入口：为指定模块生成 AI 解释

        Args:
            module: 'bazi' | 'iching' | 'guanyin' | 'liuren' | 'daily'
            data_dict: 模块输出的结构化数据（会传给 prompt builder）
            use_cache: 是否使用缓存（默认 True）

        Returns:
            AI 生成的文本，或 None（降级到静态模板）
        """
        self._init_client()
        if not self._enabled:
            return None

        # 查缓存
        if use_cache:
            cached = _cache_get(module, data_dict)
            if cached:
                return cached

        # 构建 prompt
        prompt = self._build_prompt(module, data_dict)
        if not prompt:
            return None

        # 调用 API
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.8,
                max_tokens=1200,
            )
            text = response.choices[0].message.content.strip()
            text = self._clean_output(text)
        except Exception as e:
            print(f"[AI] API 调用失败 ({module}): {e}")
            return None

        # 写缓存
        if text and use_cache:
            _cache_set(module, data_dict, text)

        return text

    @staticmethod
    def _clean_output(text):
        """清洗 AI 输出中的 markdown 格式字符"""
        import re
        # 去掉 markdown 标题符号
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
        # 去掉行首的 * - 列表符号
        text = re.sub(r'^[\*\-]\s+', '', text, flags=re.MULTILINE)
        # 去掉数字序号
        text = re.sub(r'^\d+[\.\)、]\s*', '', text, flags=re.MULTILINE)
        # 去掉行内反引号
        text = text.replace('`', '')
        # 去掉行内加粗/斜体符号
        text = text.replace('**', '').replace('__', '')
        text = text.replace('*', '').replace('_', '')
        # 去掉多余空行（保留最多两个连续换行）
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    # ---- Prompt 构建器 ----
    def _build_prompt(self, module, data):
        """根据模块类型构建 prompt"""
        builders = {
            "bazi": self._bazi_prompt,
            "iching": self._iching_prompt,
            "guanyin": self._guanyin_prompt,
            "liuren": self._liuren_prompt,
            "daily": self._daily_prompt,
        }
        builder = builders.get(module)
        if builder:
            return builder(data)
        return None

    # ==== 八字 Prompt ====
    def _bazi_prompt(self, data):
        gender = data.get("gender", "男")
        shengxiao = data.get("shengxiao", "")
        pillars = data.get("pillars", [])
        wx_counts = data.get("wuxing_counts", {})
        yongshen = data.get("yongshen", {})
        shensha = data.get("shensha", {})
        dayun = data.get("dayun", {})

        # 组装四柱信息
        pillar_lines = []
        for p in pillars:
            pillar_lines.append(
                f"  {p['name']}：{p['ganzhi']}（纳音{p.get('nayin','')}，十神：{p.get('shishen','')}，"
                f"藏干：{'、'.join(p.get('canggan',[]))}）"
            )
        pillar_text = "\n".join(pillar_lines)

        # 五行统计
        wx_text = "、".join(f"{k}{v}个" for k, v in wx_counts.items())

        # 神煞
        ss_items = []
        for k, v in shensha.items():
            val = "、".join(v) if isinstance(v, list) else str(v)
            ss_items.append(f"{k}：{val}")
        ss_text = "；".join(ss_items) if ss_items else "无特殊神煞"

        # 大运
        dy_text = f"起运{dayun.get('qiyun_age','?')}岁，{dayun.get('direction','')}"
        dayun_list = dayun.get("dayun", [])
        if dayun_list:
            dy_text += f"，首步大运{dayun_list[0]['ganzhi']}({dayun_list[0].get('nayin','')})"

        # 用神
        ys_text = f"日主{yongshen.get('day_master_wuxing','?')}，{yongshen.get('body_type','')}，"
        ys_text += f"用神为{'、'.join(yongshen.get('yongshen',[]))}"

        return f"""请为道友八字命盘做详细批注。

=== 命盘信息 ===
性别：{gender}
生肖：{shengxiao}
四柱：
{pillar_text}
五行分布：{wx_text}
{ys_text}
神煞：{ss_text}
大运：{dy_text}

请从以下角度分析：
1. 命主性情（结合日主五行和十神配置）
2. 格局高低与人生大趋势
3. 事业财运方向
4. 人际关系与感情
5. 健康注意事项
6. 大运走势简述
7. 给道友的一句道家智慧赠言

请以道长的口吻书写，300-500字。"""

    # ==== 金钱卦 Prompt ====
    def _iching_prompt(self, data):
        orig = data.get("original_hexagram", {})
        changed = data.get("changed_hexagram", {})
        changing_lines = data.get("changing_lines", [])
        num_changing = len(changing_lines)
        method = data.get("method", "")
        interpretations = data.get("interpretations", [])

        # 卦辞爻辞引用
        yao_texts = []
        for item in interpretations:
            yao_texts.append(f"[{item.get('source','')}] {item.get('text','')}")
        yao_block = "\n".join(yao_texts)

        changed_name = changed.get('name_cn', '无变卦') if changed else '无变卦'

        return f"""请为道友解这一卦。

=== 卦象信息 ===
本卦：{orig.get('name_cn','?')}（{orig.get('upper_trigram','')}上{orig.get('lower_trigram','')}下）
变卦：{changed_name}
动爻数：{num_changing}
动爻位置：{changing_lines if changing_lines else '无'}
解卦规则：{method}

=== 卦辞爻辞 ===
{yao_block}

请从以下角度分析：
1. 本卦的核心含义（用白话解释卦辞的精髓）
2. 动爻揭示的变化趋势
3. 对道友所问之事的启示
4. 注意事项与建议

请以道长的口吻书写，300-400字。"""

    # ==== 观音签 Prompt ====
    def _guanyin_prompt(self, data):
        lot = data.get("lot", {})
        confirmed = data.get("confirmed", False)

        interp_items = []
        for k, v in lot.get("interpretation", {}).items():
            interp_items.append(f"  {k}：{v}")
        interp_text = "\n".join(interp_items)

        return f"""请为道友解这支观音灵签。

=== 签文信息 ===
签号：第{lot.get('id','?')}签
等级：{lot.get('level','?')}
典故：{lot.get('title','?')}
签诗：
{lot.get('poem','?')}
判词：{lot.get('judgment','?')}

=== 分类判断 ===
{interp_text}

掷筊确认：{'已得圣杯确认' if confirmed else '未得圣杯，仅供参考'}

请从以下角度分析：
1. 签诗的白话解读和典故含义
2. 综合运势判断
3. 对道友所问之事的建议
4. 注意事项

请以道长的口吻书写，300-400字。"""

    # ==== 大六壬 Prompt ====
    def _liuren_prompt(self, data):
        sanchuan = data.get("sanchuan", {})
        sike_list = data.get("sike", [])
        shensha = data.get("shensha", {})
        tianjiang = data.get("tianjiang", {})

        # 四课信息
        sike_lines = []
        for sk in sike_list:
            sike_lines.append(f"  {sk.get('name','')}：天盘{sk.get('tianpan','')}({sk.get('tian_wx','')}) "
                              f"临地盘{sk.get('dipan','')}({sk.get('di_wx','')}) {sk.get('ke','')}")
        sike_text = "\n".join(sike_lines)

        # 三传
        chu = sanchuan.get("chu_chuan", "?")
        zhong = sanchuan.get("zhong_chuan", "?")
        mo = sanchuan.get("mo_chuan", "?")
        keti = sanchuan.get("keti", "?")

        # 天将
        tj_items = []
        for zhi, (name, wx, jx) in tianjiang.items():
            tj_items.append(f"{zhi}宫{name}({wx},{jx})")
        tj_text = "；".join(tj_items)

        # 神煞
        ss_items = []
        for k, v in shensha.items():
            val = "、".join(v) if isinstance(v, list) else str(v)
            ss_items.append(f"{k}：{val}")
        ss_text = "；".join(ss_items) if ss_items else "无特殊神煞"

        return f"""请为道友解读此大六壬课式。

=== 排盘信息 ===
占日：{data.get('day_ganzhi','?')}（日干{data.get('day_gan','?')}）
时辰：{data.get('shichen','?')}
月将：{data.get('yuejiang_name','?')}（{data.get('yuejiang','?')}）

=== 四课 ===
{sike_text}

=== 三传 ===
课体：{keti}
初传：{chu} → 中传：{zhong} → 末传：{mo}

=== 天将分布 ===
{tj_text}

=== 神煞 ===
{ss_text}

请从以下角度分析：
1. 课体总论（这个课体揭示什么性质的事？）
2. 三传走势（初传何事发端，中传如何发展，末传结局如何？）
3. 四课中干支关系揭示的现状
4. 天将吉凶布局
5. 综合判断与对道友的建议

请以道长的口吻书写，400-500字。"""

    # ==== 每日运势 Prompt ====
    def _daily_prompt(self, data):
        fortune = data.get("fortune", {})
        return f"""请为道友解读今日运势。

=== 今日信息 ===
日期：{data.get('date','?')}
干支：{data.get('ganzhi','?')}
卦象：{fortune.get('gua_name','?')}
等级：{fortune.get('level','?')}

请从财运、感情、健康、宜忌四个方面给出今日运势建议，200-300字。
以道长的口吻书写，带一句开篇问候。"""


# ============================================================
# 全局单例
# ============================================================
_interpreter = None


def get_interpreter():
    """获取全局 AI 解释器单例"""
    global _interpreter
    if _interpreter is None:
        _interpreter = AIInterpreter()
    return _interpreter
