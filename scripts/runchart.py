import matplotlib.pyplot as plt
import json
from datetime import datetime

# archivo donde guardas métricas históricas
FILE = "./metrics.json"

with open(FILE) as f:
    data = json.load(f)

dates = [int(d["week"]) for d in data]
values = [d["value"] for d in data]

plt.figure()
plt.plot(dates, values, marker="o")
plt.title("Run Chart")
plt.xlabel("Week")
plt.ylabel("Issues")
plt.grid(True)

current_year_month = datetime.now().strftime("%Y-%m")
plt.savefig(f"run_chart-{current_year_month}.png")