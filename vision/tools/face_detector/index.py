from .components import detect_and_track

def process_frame(img, target_angles, last_send_time):
    return detect_and_track(img, target_angles, last_send_time)
