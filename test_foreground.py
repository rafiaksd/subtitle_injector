import win32gui
import win32con
import cv2, time
import pyautogui

# Global for crop
drawing = False
ix, iy, ex, ey = -1, -1, -1, -1
rect_defined = False

def bring_window_to_front(window_title):
    hwnd = win32gui.FindWindow(None, window_title)
    if hwnd:
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        rect = win32gui.GetWindowRect(hwnd)
        x = rect[0] + 10
        y = rect[1] + 10
        pyautogui.click(x, y)  # Simulate click inside the window
        time.sleep(0.2)
        win32gui.SetForegroundWindow(hwnd)
    else:
        print(f"Window '{window_title}' not found.")

def select_crop_area(video_path):
    def draw_rectangle(event, x, y, flags, param):
        global ix, iy, ex, ey, drawing, rect_defined
        if event == cv2.EVENT_LBUTTONDOWN:
            drawing = True
            ix, iy = x, y
            ex, ey = x, y
        elif event == cv2.EVENT_MOUSEMOVE and drawing:
            ex, ey = x, y
            rect_defined = True
        elif event == cv2.EVENT_LBUTTONUP:
            drawing = False
            ex, ey = x, y
            rect_defined = True

    global ix, iy, ex, ey, rect_defined
    cap = cv2.VideoCapture(video_path)
    frame_index = 0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    if not cap.isOpened():
        print("Error opening video.")
        return

    cv2.namedWindow("Video Crop Selector")
    bring_window_to_front("Video Crop Selector")
    cv2.setMouseCallback("Video Crop Selector", draw_rectangle)

    while True:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        ret, frame = cap.read()
        if not ret:
            break

        display_frame = frame.copy()
        if drawing or rect_defined:
            cv2.rectangle(display_frame, (ix, iy), (ex, ey), (0, 255, 0), 2)

        cv2.putText(display_frame, f"Frame {frame_index+1}/{total_frames}", (10, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        cv2.imshow("Video Crop Selector", display_frame)

        key = cv2.waitKey(0)
        if key == ord('c') and rect_defined:
            cv2.destroyAllWindows()
            return (min(ix, ex), min(iy, ey), abs(ex - ix), abs(ey - iy))
        elif key == ord('a'):
            frame_index = max(frame_index - 20, 0)
        elif key == ord('d'):
            frame_index = min(frame_index + 20, total_frames - 1)

    cap.release()
    cv2.destroyAllWindows()

crop_x, crop_y, crop_w, crop_h = select_crop_area("testing_vert_burn_onego.mp4")
print(crop_x, crop_y, crop_w, crop_y)