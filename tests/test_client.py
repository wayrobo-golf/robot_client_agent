import requests
import json
import time

API_URL = "http://localhost:8000/api/v1/chat"

# 模拟机器人持续上报的状态
robot_state = {
    "battery": 65,
    "is_charging": False,
    "current_location": "A区草坪",
    "basket_capacity": 90,
    "hardware_status": "normal"
}

def send_message(text: str):
    print(f"\n👨‍💼 用户: {text}")
    payload = {
        "user_id": "noah_260409_v3",
        "robot_id": "golf_bot_01",
        "text": text,
        "state": robot_state
    }
    
    start_time = time.time()
    response = requests.post(API_URL, json=payload)
    latency = time.time() - start_time
    
    if response.status_code == 200:
        data = response.json()
        print(f"🤖 机器人语音回复: {data['tts_text']}")
        print(f"⚙️  触发动作模块: {data['executed_actions']}")
        print(f"⏱️  请求耗时: {latency:.3f} 秒")
    else:
        print(f"❌ 请求失败: {response.status_code} - {response.text}")

if __name__ == "__main__":
    print("=== 开始模拟高尔夫机器人多轮交互 ===")
    
    # 第一轮：故意不说去哪个站卸球
    send_message("球篓快满了，帮我把球卸了。")
    time.sleep(2)
    
    # 第二轮：补全信息。如果 Agent 记住了上一轮，它会知道“2号”指的是卸球站
    send_message("就去 2 号吧。")
    time.sleep(2)
    
    # 第三轮：测试强行触发急停模块
    send_message("有人冲过来了，快停下！")