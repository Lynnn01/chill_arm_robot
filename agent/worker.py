import asyncio
import sys

def redirect_print_to_queue(log_q):
    class QueueWriter:
        def write(self, msg):
            if msg:
                log_q.put(msg)
        def flush(self):
            pass
    sys.stdout = QueueWriter()
    sys.stderr = QueueWriter()

def isolated_agent_worker(input_q, log_q, cmd_q, res_q):
    """
    Entry point for the isolated AI process.
    """
    # 1. Setup RPC before importing ANY hardware code
    from hardware.rpc import setup_rpc_queues
    setup_rpc_queues(cmd_q, res_q)
    
    # 2. Redirect prints to the GUI log queue
    redirect_print_to_queue(log_q)
    
    # 3. Import agent logic (this will trigger hardware.init -> RPC Proxy)
    from agent.agent import get_agent, get_contextual_input
    from agents import Runner
    
    agent = get_agent()
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    while True:
        try:
            user_input = input_q.get()
            try:
                contextual_input = get_contextual_input(user_input)
                result = loop.run_until_complete(Runner.run(agent, input=contextual_input))
                ai_reply = result.final_output
                print(f"\n🤖 <LLM>: {ai_reply}\n")
            except Exception as e:
                print(f"\n⚠️ <ERROR>: {e}\n")
            finally:
                # Signal the GUI that processing is done
                log_q.put(("ENABLE_INPUTS", True))
        except Exception as e:
            print(f"Worker critical loop error: {e}")
