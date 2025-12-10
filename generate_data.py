import csv
import random
from datetime import datetime, timedelta

def generate_robot_data(
    output_file: str = "robot_sensor_data.csv",
    days: int = 30,
    interval_minutes: int = 10,
    random_seed: int = 42,
):
    random.seed(random_seed)

    # 基本参数
    robots = [f"Robot_{i:02d}" for i in range(1, 11)]
    points_per_day = int(24 * 60 / interval_minutes)  # 144
    total_points = days * points_per_day               # 4320

    # 时间范围：过去 30 天
    end_time = datetime.now().replace(second=0, microsecond=0)
    start_time = end_time - timedelta(days=days)
    timestamps = [
        start_time + timedelta(minutes=i * interval_minutes)
        for i in range(total_points)
    ]

    # 随机选 2 台机器人作为故障机器人
    fault_robots = random.sample(robots, 2)

    # 为每个故障机器人定义：故障发生时间索引 + 线性上升的起始/结束值
    fault_plan = {}
    min_ramp_points = int(24 * 60 / interval_minutes)  # 24 小时对应的点数 = 144

    # 确保有足够数据进行 24 小时线性上升
    valid_failure_indices = list(range(min_ramp_points, total_points))

    for r in fault_robots:
        failure_index = random.choice(valid_failure_indices)
        ramp_start_index = failure_index - min_ramp_points

        # 线性上升起始/结束的目标值（可超过“正常范围”，模拟异常）
        start_temp = random.uniform(60, 70)             # 从接近上限开始
        end_temp = start_temp + random.uniform(10, 25)  # 升到 70~100 左右

        start_vib = random.uniform(3.0, 4.5)            # 接近上限
        end_vib = start_vib + random.uniform(2.0, 4.0)  # 升到 5 以上

        fault_plan[r] = {
            "ramp_start": ramp_start_index,
            "failure_index": failure_index,
            "start_temp": start_temp,
            "end_temp": end_temp,
            "start_vib": start_vib,
            "end_vib": end_vib,
        }

    def clip(value, low, high):
        return max(low, min(high, value))

    # 写 CSV
    with open(output_file, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Timestamp",
            "Robot_ID",
            "Motor_Temperature",
            "Vibration_Level",
            "Current_Load",
            "Status",
        ])

        for robot in robots:
            is_fault_robot = robot in fault_plan
            fp = fault_plan.get(robot, None)

            for idx, ts in enumerate(timestamps):
                # --------- 正常数据的基础分布（正常范围）---------
                motor_temp = clip(random.gauss(55, 5), 40, 70)   # 正常 40-70℃
                vibration = clip(random.gauss(2.5, 1), 0, 5)     # 正常 0-5 mm/s
                current_load = clip(random.gauss(6, 2), 2, 10)   # 正常 2-10 A

                # 正常状态分布（非故障阶段）
                status = random.choices(
                    population=["Running", "Idle", "Warning"],
                    weights=[0.8, 0.15, 0.05],
                    k=1
                )[0]

                # --------- 故障逻辑覆盖 ---------
                if is_fault_robot:
                    ramp_start = fp["ramp_start"]
                    failure_index = fp["failure_index"]
                    start_temp = fp["start_temp"]
                    end_temp = fp["end_temp"]
                    start_vib = fp["start_vib"]
                    end_vib = fp["end_vib"]

                    if idx < ramp_start:
                        # 故障前很早的阶段：正常运行
                        # 保持前面的 motor_temp / vibration / current_load
                        pass

                    elif ramp_start <= idx <= failure_index:
                        # 故障前 24 小时：温度 & 振动线性上升
                        frac = (idx - ramp_start) / (failure_index - ramp_start)

                        motor_temp = start_temp + frac * (end_temp - start_temp)
                        motor_temp += random.gauss(0, 0.5)  # 加一点小噪声

                        vibration = start_vib + frac * (end_vib - start_vib)
                        vibration += random.gauss(0, 0.1)

                        # 故障前的阶段标为 Warning，最后一点为 Error
                        if idx < failure_index:
                            status = "Warning"
                        else:
                            status = "Error"

                        # 故障前/故障时电流负载略有升高
                        current_load = clip(
                            current_load + random.uniform(1.0, 3.0),
                            2,
                            14
                        )

                    else:  # idx > failure_index
                        # 故障之后：维持在高温高振动 + Error 状态
                        motor_temp = end_temp + random.gauss(0, 1.0)
                        vibration = end_vib + random.gauss(0, 0.2)
                        current_load = clip(
                            current_load + random.uniform(1.0, 3.0),
                            2,
                            14
                        )
                        status = "Error"

                writer.writerow([
                    ts.strftime("%Y-%m-%d %H:%M:%S"),
                    robot,
                    round(motor_temp, 2),
                    round(vibration, 3),
                    round(current_load, 3),
                    status,
                ])

    print(f"数据已生成到 {output_file}")
    print(f"埋入故障的机器人：{', '.join(fault_robots)}")

if __name__ == "__main__":
    generate_robot_data()
# generate_data.py