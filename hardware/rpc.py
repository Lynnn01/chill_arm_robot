import multiprocessing
import time
import uuid

# Global Queues for RPC
cmd_queue = None
res_queue = None

def setup_rpc_queues(cq, rq):
    global cmd_queue, res_queue
    cmd_queue = cq
    res_queue = rq

class RPCClient:
    def _call(self, target, method, *args, **kwargs):
        if cmd_queue is None or res_queue is None:
            raise RuntimeError("RPC Queues not initialized in this process")
        
        req_id = str(uuid.uuid4())
        req = {
            "id": req_id,
            "target": target,
            "method": method,
            "args": args,
            "kwargs": kwargs
        }
        cmd_queue.put(req)
        
        # Wait for response
        while True:
            res = res_queue.get()
            if res["id"] == req_id:
                if res.get("error"):
                    raise Exception(res["error"])
                return res["result"]
            else:
                res_queue.put(res)
                time.sleep(0.01)

class MyCobotRPCProxy(RPCClient):
    def send_angles(self, angles, speed): return self._call("mc", "send_angles", angles, speed)
    def send_angle(self, id, degree, speed): return self._call("mc", "send_angle", id, degree, speed)
    def send_coords(self, coords, speed, mode): return self._call("mc", "send_coords", coords, speed, mode)
    def get_coords(self): return self._call("mc", "get_coords")
    def get_angles(self): return self._call("mc", "get_angles")
    def release_all_servos(self): return self._call("mc", "release_all_servos")
    def set_color(self, r, g, b): return self._call("mc", "set_color", r, g, b)
    def set_gripper_value(self, val, speed): return self._call("mc", "set_gripper_value", val, speed)
    def set_fresh_mode(self, mode): return self._call("mc", "set_fresh_mode", mode)

class CameraManagerRPCProxy(RPCClient):
    def get_frame(self): return self._call("cam", "get_frame")
    
class HardwareInitRPCProxy(RPCClient):
    def open_gripper(self): return self._call("init", "open_gripper")
    def close_gripper(self): return self._call("init", "close_gripper")
    
    @property
    def is_holding_object(self): return self._call("init", "get_is_holding")
    @is_holding_object.setter
    def is_holding_object(self, v): self._call("init", "set_is_holding", v)
    
    @property
    def current_held_object(self): return self._call("init", "get_current_held")
    @current_held_object.setter
    def current_held_object(self, v): self._call("init", "set_current_held", v)
    
    @property
    def known_objects(self): return self._call("init", "get_known_objects")
    @known_objects.setter
    def known_objects(self, v): self._call("init", "set_known_objects", v)

def run_rpc_server(cmd_q, res_q):
    import hardware.init as hw
    print("RPC Server listening for hardware commands...")
    while True:
        try:
            req = cmd_q.get()
            target = req["target"]
            method = req["method"]
            args = req.get("args", [])
            kwargs = req.get("kwargs", {})
            
            res = {"id": req["id"], "result": None, "error": None}
            
            try:
                if target == "mc":
                    obj = hw.mc
                    func = getattr(obj, method)
                    res["result"] = func(*args, **kwargs)
                elif target == "cam":
                    obj = hw.cam_manager
                    func = getattr(obj, method)
                    res["result"] = func(*args, **kwargs)
                elif target == "init":
                    if method == "get_is_holding": res["result"] = hw.is_holding_object
                    elif method == "set_is_holding": hw.is_holding_object = args[0]
                    elif method == "get_current_held": res["result"] = hw.current_held_object
                    elif method == "set_current_held": hw.current_held_object = args[0]
                    elif method == "get_known_objects": res["result"] = hw.known_objects
                    elif method == "set_known_objects": hw.known_objects = args[0]
                    else:
                        func = getattr(hw, method)
                        res["result"] = func(*args, **kwargs)
            except Exception as e:
                res["error"] = str(e)
                
            res_q.put(res)
        except Exception as e:
            print(f"RPC Server Exception: {e}")
            time.sleep(1)
