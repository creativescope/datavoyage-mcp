# 素材查询参数与结果指引

适用范围：助手选择工具、准备参数和解释素材查询结果时读取。必须核对实时 schema，禁止凭旧描述添加不存在的参数。

## 工具选择流程

综合筛选使用 `search_materials_v2`；简单查询已确认游戏的素材可用 `get_game_materials`。两者参数不同，不能混用。详情使用 `get_material_detail_v2`；游戏身份解析使用 `search_games` 或 `resolve_game_by_identifier`。

`search_materials_v2` 至少需要 game_ids、keyword、country_codes、publisher_platforms、languages 中一个主体条件；仅日期、素材类型或时长不够。未指定日期时默认近 90 天，未指定数量时 20 条，必须向用户说明采用的默认范围。不得为凑结果自动扩大范围。

## 综合筛选参数

| 参数 | 含义与取值 |
| --- | --- |
| `game_ids` | 游戏搜索返回的令牌数组，最多 20 个；不是游戏名或包名 |
| `keyword` | 素材文本匹配词，最多 100 字符；不是自由视觉语义检索 |
| `country_codes` | 国家代码数组，最多 20 个，先按筛选器映射 |
| `country_match` | contains 默认命中任一所选国家；exclusive 要求素材国家集合完全一致，不是“同时包含” |
| `publisher_platforms` | 渠道数组，采用 get_filter_options 的 platform 标准值 |
| `material_types` | image、video、playable 字符串数组 |
| `video_type` | 0 图片、1 视频、2 试玩；与 material_types 二选一 |
| `languages` | 数据标准语言值数组，精确匹配；不把 country 筛选器当语言字典，不确定时询问或省略并说明 |
| `aspect_ratio` | landscape 横屏、portrait 竖屏、square 方形 |
| `duration_min_seconds` | 时长下限，包含边界，大于等于 0 |
| `duration_max_seconds` | 时长上限，不含边界，必须大于 0 且大于下限；“30 秒以内”与“少于30秒”需区分 |
| `device` | ios、android；不传或 all 不限 |
| `quality` | hd 短边至少720像素，sd 低于720像素；不传或 all 不限 |
| `only_discover` | true 为首次发现日期落入区间；false 或省略为生命周期与区间重叠，不保证当前仍在投放 |
| `date_from` / `date_to` | YYYY-MM-DD；相对时间以 get_context 返回日期解释 |
| `sort_by` | heat 热度（默认）、latest 最新投放、ending 最近结束、reinvestment 复投优先；复投排序不是只查复投 |
| `limit` / `offset` | 每页默认20、最多50；偏移默认0，不为统计总数遍历全部页 |

平台值包括 facebook、instagram、messenger、audience_network、threads、admob、youtube、tiktok、mintegral、unity、applovin、ironsource、vungle、pangle；以实时筛选器为准。

## 游戏素材与详情

`get_game_materials` 必须传 `game_id`，可传 date_from、date_to、publisher_platform（单值）、video_type、sort_by、limit、offset，limit 上限100；执行前以目录的实际属性名复核。需要国家、语言、画面比例等额外筛选时改用综合查询。

详情传服务返回的完整 `detail_url`，`include` 可为 summary、media。详情返回媒体地址用于查看或播放；不能将媒体地址作为 detail_url 传回。用户提供非服务生成链接时不要自行拼接查询令牌。

## 结果口径与验收

国家筛选表示素材关联该投放市场，不表示曝光按国家拆分。热度、复投、媒体展示不足以证明广告转化效果。未观看媒体时不得编写视频剧情、开场钩子或画面点评。

素材结果有 `has_more`，没有精确匹配总数。明确区分“本页20条”和“共20条”。用户要求追加时按原筛选翻页，达到请求数量或 has_more=false 即停止。链接失效、字段缺失或查询无结果须原样说明，禁止换一款游戏或放宽条件而不告知。
