# src/core/config.py

ROBOT_TOOLS_REGISTRY = [
    # ==========================================
    # 一、 基础作业指令 (Job & Operation)
    # ==========================================
    {
        "id": "job_001",
        "name": "start_collecting",
        "description": "指令机器人开始执行高尔夫球捡球作业。可指定特定区域（如练习场、1号洞）。",
        "parameters": {
            "type": "object",
            "properties": {
                "zone_name": {
                    "type": "string",
                    "description": "选填，要清扫的高尔夫球场区域名称。如'练习场', 'A区', '全局'"
                }
            }
        },
        "search_keywords": ["开始工作", "捡球", "去干活", "打扫", "出发", "收球", "开工", "启动作业"]
    },
    {
        "id": "job_002",
        "name": "stop_collecting",
        "description": "结束当前的捡球工作，机器人在当前位置原地待命。",
        "parameters": {"type": "object", "properties": {}},
        "search_keywords": ["结束工作", "停下来", "别干了", "停止作业", "原地待命", "下班"]
    },
    {
        "id": "job_003",
        "name": "unload_golf_balls",
        "description": "球篓已满或收到指令时，前往指定的卸球站进行自动卸球流程。",
        "parameters": {
            "type": "object",
            "properties": {
                "station_id": {
                    "type": "string",
                    "description": "选填，指定卸球站点的编号"
                }
            }
        },
        "search_keywords": ["卸球", "倒球", "球满了", "清空球篓", "去倒垃圾", "去排球", "卸载"]
    },
    {
        "id": "job_004",
        "name": "go_to_charge",
        "description": "控制机器人返回充电桩进行充电。",
        "parameters": {"type": "object", "properties": {}},
        "search_keywords": ["充电", "没电了", "回充", "去充电", "找插座", "电量低", "回基站"]
    },

    # ==========================================
    # 二、 异常处理与底层控制 (Recovery & Hardware)
    # ==========================================
    {
        "id": "hw_001",
        "name": "wake_up",
        "description": "将机器人从睡眠状态唤醒，准备接受工作指令。",
        "parameters": {"type": "object", "properties": {}},
        "search_keywords": ["睡眠唤醒", "醒醒", "开机", "起来", "唤醒系统"]
    },
    {
        "id": "hw_002",
        "name": "enter_sleep_mode",
        "description": "控制机器人进入低功耗睡眠模式。",
        "parameters": {"type": "object", "properties": {}},
        "search_keywords": ["进入睡眠", "睡觉", "休眠", "关机待机", "低功耗"]
    },
    {
        "id": "hw_003",
        "name": "execute_recovery",
        "description": "当机器人陷入沙坑、泥地或被卡住时，执行脱困摇摆或倒车流程试图恢复行驶。",
        "parameters": {"type": "object", "properties": {}},
        "search_keywords": ["脱困", "卡住了", "出不来", "陷进去了", "打滑", "摇一摇", "卡死"]
    },
    {
        "id": "hw_004",
        "name": "reboot_robot",
        "description": "重启机器人上位机及整车控制系统。",
        "parameters": {"type": "object", "properties": {}},
        "search_keywords": ["重启机器人", "重启整车", "死机了", "重新启动系统"]
    },
    {
        "id": "hw_005",
        "name": "reboot_m2_module",
        "description": "单独重启组合导航 M2 模组，用于解决卫星丢失、RTK不固定或定位漂移问题。",
        "parameters": {"type": "object", "properties": {}},
        "search_keywords": ["重启导航", "重启M2", "定位丢了", "位置不对", "瞎了", "没有GPS", "RTK掉线", "卫星信号差"]
    },

    # ==========================================
    # 三、 导航、避障与建图 (Navigation & Mapping)
    # ==========================================
    {
        "id": "nav_001",
        "name": "replan_path",
        "description": "强制机器人丢弃当前路径，基于当前位置重新进行全局路径规划。",
        "parameters": {"type": "object", "properties": {}},
        "search_keywords": ["重新规划", "换条路", "路走不通", "绕路", "更新路线"]
    },
    {
        "id": "nav_002",
        "name": "trigger_obstacle_avoidance",
        "description": "开启或调整避障策略，处理前方的动态或静态障碍物。",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["enable", "disable", "force_bypass"],
                    "description": "避障操作：开启、关闭或强制绕行"
                }
            }
        },
        "search_keywords": ["避障", "躲开", "前面有人", "绕过去", "躲避"]
    },
    {
        "id": "nav_003",
        "name": "delete_obstacle",
        "description": "在代价地图(Costmap)中强制清除指定的或前方的虚拟障碍物，通常用于消除“幽灵障碍物”（如其实是一簇高草被误认）。",
        "parameters": {"type": "object", "properties": {}},
        "search_keywords": ["删除障碍物", "清除障碍", "前面没东西", "假障碍", "开出一条路", "忽略草丛", "强行通过"]
    },
    {
        "id": "nav_004",
        "name": "remap_environment",
        "description": "清除旧地图，开启激光雷达或视觉传感器重新对当前场地进行SLAM建图。",
        "parameters": {"type": "object", "properties": {}},
        "search_keywords": ["重新建图", "扫描场地", "更新地图", "重绘地图", "地图不对"]
    },

    # ==========================================
    # 四、 [AI补充] 核心运维与安全指令 (Status & Safety)
    # ==========================================
    {
        "id": "sys_001",
        "name": "emergency_stop",
        "description": "【高优先级】触发急停机制，立刻切断动力底盘输出，机器人原地锁死。",
        "parameters": {"type": "object", "properties": {}},
        "search_keywords": ["急停", "救命", "停下", "别动", "危险", "刹车", "快停", "撞了"]
    },
    {
        "id": "sys_002",
        "name": "check_status",
        "description": "查询机器人的当前综合状态，包括电量、当前坐标、是否正在工作以及故障码。",
        "parameters": {"type": "object", "properties": {}},
        "search_keywords": ["状态", "你在哪", "电量多少", "还有电吗", "坏了吗", "在干嘛", "报告情况"]
    },
    {
        "id": "sys_003",
        "name": "check_basket_capacity",
        "description": "检查当前高尔夫球篓的装载率（满了没有）。",
        "parameters": {"type": "object", "properties": {}},
        "search_keywords": ["捡了多少球", "球篓满了没", "还能装吗", "检查容量", "进度如何"]
    },
    {
        "id": "sys_004",
        "name": "return_to_standby_area",
        "description": "控制机器人返回待命区（非充电桩，非卸球点，仅用于泊车）。",
        "parameters": {"type": "object", "properties": {}},
        "search_keywords": ["回去", "回车库", "待命", "撤退", "靠边停车", "别挡路"]
    }
]

# 定义每次对话都必须强行带上的“保命”常驻工具（通常是急停和查状态）
STATIC_TOOL_NAMES = ["emergency_stop", "check_status"]


