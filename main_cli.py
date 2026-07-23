import os
import sys
import asyncio

# catlazy: [reuse] แอด Path ให้เจาะเข้าโฟลเดอร์ root ได้ง่ายๆ
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# catlazy: [reuse] นำโค้ด Interactive CLI ของเดิมมาใช้เลย ไม่ต้องเขียนใหม่
from agent.agent import main

if __name__ == "__main__":
    print("🤖 <SYSTEM>: Starting CLI Mode...")
    asyncio.run(main())
