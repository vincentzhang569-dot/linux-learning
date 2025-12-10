import json
import time
from datetime import datetime
import random
import re

class RobotController:
    def __init__(self, num_robots=5):
        self.num_robots = num_robots
        self.robots = {}
        self._initialize_robots()

    def _initialize_robots(self):
        for i in range(1, self.num_robots + 1):
            self.robots[i] = {
                "id": i,
                "status": "Running",
                "speed": random.randint(60, 90),
                "temperature": random.randint(40, 60),
                "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

    def _clean_int(self, value):
        """强力参数清洗"""
        try:
            if isinstance(value, int): return value
            if isinstance(value, float): return int(value)
            if isinstance(value, str):
                digits = re.findall(r'-?\d+', value)
                if digits: return int(digits[0])
            return None
        except: return None

    def get_all_status(self):
        self._simulate_fluctuation()
        return self.robots

    # --- 基础原子动作 ---

    def get_status(self, robot_id, **kwargs):
        r_id = self._clean_int(robot_id)
        if r_id in self.robots: return self.robots[r_id]
        return {"error": "ID不存在"}

    def emergency_stop(self, robot_id, **kwargs):
        try:
            r_id = self._clean_int(robot_id)
            if r_id not in self.robots: return {"success": False, "message": "ID不存在"}
            self.robots[r_id]["status"] = "Emergency_Stop"
            self.robots[r_id]["speed"] = 0
            self.robots[r_id]["last_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return {"success": True, "message": f"#{r_id} 已急停", "data": self.robots[r_id]}
        except Exception as e: return {"success": False, "message": str(e)}

    def adjust_speed(self, robot_id, speed, **kwargs):
        try:
            r_id = self._clean_int(robot_id)
            spd = self._clean_int(speed)
            if r_id not in self.robots: return {"success": False, "message": "ID不存在"}
            
            if self.robots[r_id]["status"] == "Emergency_Stop":
                 return {"success": False, "message": "无法调速：处于急停锁定中，请先使用【一键启动】或【重置】。"}

            if spd > 100: spd = 100
            if spd < 0: spd = 0
            self.robots[r_id]["speed"] = spd
            self.robots[r_id]["status"] = "Running" if spd > 0 else "Stopped"
            self.robots[r_id]["last_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return {"success": True, "message": f"#{r_id} 速度设为 {spd}", "data": self.robots[r_id]}
        except Exception as e: return {"success": False, "message": str(e)}

    def reset_system(self, robot_id, **kwargs):
        try:
            r_id = self._clean_int(robot_id)
            if r_id not in self.robots: return {"success": False, "message": "ID不存在"}
            self.robots[r_id]["status"] = "Running"
            self.robots[r_id]["speed"] = 50
            self.robots[r_id]["temperature"] = 45
            self.robots[r_id]["last_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return {"success": True, "message": f"#{r_id} 系统已重置", "data": self.robots[r_id]}
        except Exception as e: return {"success": False, "message": str(e)}

    # --- 🔥 核心大招：宏指令 (Macro Command) ---
    def startup_system(self, robot_id, target_speed=50, **kwargs):
        """一键启动：自动解除急停 + 设置速度"""
        try:
            r_id = self._clean_int(robot_id)
            spd = self._clean_int(target_speed)
            if spd is None: spd = 50 # 默认速度
            
            if r_id not in self.robots: return {"success": False, "message": "ID不存在"}
            
            # 1. 强制解除急停
            self.robots[r_id]["status"] = "Running"
            self.robots[r_id]["temperature"] = 45 # 顺便重置温度
            
            # 2. 设置目标速度
            self.robots[r_id]["speed"] = spd
            self.robots[r_id]["last_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            return {"success": True, "message": f"#{r_id} 已执行【一键启动】程序，当前速度 {spd}", "data": self.robots[r_id]}
        except Exception as e: return {"success": False, "message": str(e)}

    def _simulate_fluctuation(self):
        for r_id, data in self.robots.items():
            if data["status"] == "Running":
                data["temperature"] = round(data["temperature"] + random.uniform(-0.5, 0.5), 1)